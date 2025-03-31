"""Tests for the Wikipedia GDP crawler."""

import asyncio
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from src.crawler import WikipediaGDPCrawler
from src.models import GDPGrowthRate, GDPPerCapita, WikipediaGDPData
from src.parser import WikipediaParser


@pytest.fixture
def sample_html_per_capita() -> str:
    """Return sample HTML for GDP per capita."""
    return """
    <html>
        <table class="wikitable">
            <tr><th>Rank</th><th>Country</th><th>GDP per capita</th></tr>
            <tr><td>1</td><td>Luxembourg</td><td>128,572</td></tr>
            <tr><td>2</td><td>Ireland</td><td>94,392</td></tr>
        </table>
    </html>
    """


@pytest.fixture
def sample_html_growth_rate() -> str:
    """Return sample HTML for GDP growth rate."""
    return """
    <html>
        <table class="wikitable">
            <tr><th>Rank</th><th>Country</th><th>Growth rate</th></tr>
            <tr><td>1</td><td>Guyana</td><td>62.3%</td></tr>
            <tr><td>2</td><td>Libya</td><td>17.9%</td></tr>
        </table>
    </html>
    """


@pytest.fixture
def mock_parser() -> MagicMock:
    """Create a mock parser with predefined return values."""
    parser = MagicMock(spec=WikipediaParser)
    
    # Mock GDP per capita parsing
    parser.parse_gdp_per_capita.return_value = [
        GDPPerCapita(country="Luxembourg", rank=1, gdp_per_capita=128572, year=2023),
        GDPPerCapita(country="Ireland", rank=2, gdp_per_capita=94392, year=2023),
    ]
    
    # Mock GDP growth rate parsing
    parser.parse_gdp_growth_rate.return_value = [
        GDPGrowthRate(country="Guyana", rank=1, growth_rate_percent=62.3, year=2023),
        GDPGrowthRate(country="Libya", rank=2, growth_rate_percent=17.9, year=2023),
    ]
    
    return parser


class TestWikipediaGDPCrawler:
    """Tests for the WikipediaGDPCrawler class."""
    
    def test_init(self) -> None:
        """Test crawler initialization."""
        crawler = WikipediaGDPCrawler()
        assert isinstance(crawler.parser, WikipediaParser)
        assert crawler.gdp_per_capita_url == "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)_per_capita"
        assert crawler.gdp_growth_rate_url == "https://en.wikipedia.org/wiki/List_of_countries_by_real_GDP_growth_rate"
        assert crawler.timeout > 0
        assert crawler.user_agent != ""
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self) -> None:
        """Test successful page fetching."""
        crawler = WikipediaGDPCrawler()
        
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.text = "Sample HTML content"
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response
        
        result = await crawler.fetch_page("https://example.com", mock_client)
        
        # Assert request was made properly
        mock_client.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        
        # Assert we got the expected content
        assert result == "Sample HTML content"
    
    @pytest.mark.asyncio
    async def test_fetch_page_http_error(self) -> None:
        """Test page fetching with HTTP error."""
        crawler = WikipediaGDPCrawler()
        
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.HTTPError("HTTP Error")
        
        result = await crawler.fetch_page("https://example.com", mock_client)
        
        # Assert request was attempted
        mock_client.get.assert_called_once()
        
        # Assert we got None because of the error
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_page_general_error(self) -> None:
        """Test page fetching with a general error."""
        crawler = WikipediaGDPCrawler()
        
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = Exception("General Error")
        
        result = await crawler.fetch_page("https://example.com", mock_client)
        
        # Assert request was attempted
        mock_client.get.assert_called_once()
        
        # Assert we got None because of the error
        assert result is None
    
    @pytest.mark.asyncio
    async def test_crawl(
        self, 
        mock_parser: MagicMock, 
        sample_html_per_capita: str, 
        sample_html_growth_rate: str
    ) -> None:
        """Test the crawl method with mocked responses."""
        # Create crawler with mock parser
        crawler = WikipediaGDPCrawler()
        crawler.parser = mock_parser
        
        # Mock fetch_page method to return sample HTML
        async def mock_fetch_page(url: str, _: httpx.AsyncClient) -> str:
            if url == crawler.gdp_per_capita_url:
                return sample_html_per_capita
            elif url == crawler.gdp_growth_rate_url:
                return sample_html_growth_rate
            return ""
        
        crawler.fetch_page = mock_fetch_page  # type: ignore
        
        # Run the crawler
        result = await crawler.crawl()
        
        # Check the result
        assert isinstance(result, WikipediaGDPData)
        assert len(result.per_capita) == 2
        assert len(result.growth_rates) == 2
        
        # Verify parser was called correctly
        mock_parser.parse_gdp_per_capita.assert_called_once_with(sample_html_per_capita)
        mock_parser.parse_gdp_growth_rate.assert_called_once_with(sample_html_growth_rate)
        
        # Check combined data
        assert "Luxembourg" in result.combined_data
        assert "Ireland" in result.combined_data
        assert "Guyana" in result.combined_data
        assert "Libya" in result.combined_data
    
    @pytest.mark.asyncio
    async def test_crawl_with_fetch_error(self, mock_parser: MagicMock) -> None:
        """Test crawl method when fetch_page returns None."""
        # Create crawler with mock parser
        crawler = WikipediaGDPCrawler()
        crawler.parser = mock_parser
        
        # Mock fetch_page to return None (error case)
        async def mock_fetch_page_error(url: str, _: httpx.AsyncClient) -> None:
            return None
        
        crawler.fetch_page = mock_fetch_page_error  # type: ignore
        
        # Run the crawler
        result = await crawler.crawl()
        
        # Check the result
        assert isinstance(result, WikipediaGDPData)
        assert len(result.per_capita) == 0
        assert len(result.growth_rates) == 0
        
        # Verify parser was not called
        mock_parser.parse_gdp_per_capita.assert_not_called()
        mock_parser.parse_gdp_growth_rate.assert_not_called()
    
    def test_save_to_json(self, tmp_path: str, mock_parser: MagicMock) -> None:
        """Test saving data to JSON file."""
        # Create test data
        per_capita = [
            GDPPerCapita(country="Luxembourg", rank=1, gdp_per_capita=128572, year=2023),
        ]
        
        growth_rates = [
            GDPGrowthRate(country="Guyana", rank=1, growth_rate_percent=62.3, year=2023),
        ]
        
        data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
        data.combine_data()
        
        # Create crawler
        crawler = WikipediaGDPCrawler()
        
        # Save to a temporary file
        temp_file = f"{tmp_path}/test_output.json"
        crawler.save_to_json(data, temp_file)
        
        # Verify file exists
        import os
        assert os.path.exists(temp_file) 