"""Tests for the command-line interface."""

import argparse
import io
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cli import main, parse_args, print_summary, setup_logging
from src.crawler import WikipediaGDPCrawler
from src.models import CountryStats, GDPGrowthRate, GDPPerCapita, WikipediaGDPData


def test_setup_logging() -> None:
    """Test the setup_logging function."""
    # Test with verbose=False (default)
    with patch("logging.basicConfig") as mock_basicConfig:
        setup_logging(verbose=False)
        mock_basicConfig.assert_called_once()
        args, kwargs = mock_basicConfig.call_args
        assert kwargs["level"] == 20  # INFO level
    
    # Test with verbose=True
    with patch("logging.basicConfig") as mock_basicConfig:
        setup_logging(verbose=True)
        mock_basicConfig.assert_called_once()
        args, kwargs = mock_basicConfig.call_args
        assert kwargs["level"] == 10  # DEBUG level


def test_parse_args() -> None:
    """Test the argument parser."""
    # Test with default arguments
    with patch("sys.argv", ["wiki-gdp"]):
        args = parse_args()
        assert args.output == "gdp_data.json"
        assert not args.verbose
        assert not args.pretty
        assert not args.summary
        assert args.top == 10
    
    # Test with custom arguments
    with patch("sys.argv", [
        "wiki-gdp",
        "-o", "custom.json",
        "-v",
        "--pretty",
        "--summary",
        "--top", "5"
    ]):
        args = parse_args()
        assert args.output == "custom.json"
        assert args.verbose
        assert args.pretty
        assert args.summary
        assert args.top == 5


def test_print_summary() -> None:
    """Test the summary printing function."""
    # Create test data
    country_data = {
        "Country A": CountryStats(
            country="Country A",
            gdp_per_capita=50000.0,
            gdp_per_capita_rank=1,
            gdp_growth_rate=2.5,
            gdp_growth_rate_rank=3
        ),
        "Country B": CountryStats(
            country="Country B",
            gdp_per_capita=40000.0,
            gdp_per_capita_rank=2,
            gdp_growth_rate=3.5,
            gdp_growth_rate_rank=2
        ),
        "Country C": CountryStats(
            country="Country C",
            gdp_per_capita=30000.0,
            gdp_per_capita_rank=3,
            gdp_growth_rate=4.5,
            gdp_growth_rate_rank=1
        )
    }
    
    # Capture stdout
    original_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    try:
        print_summary(country_data, top_n=2)
        output = captured_output.getvalue()
        
        # Check that we see the expected sections
        assert "Top Countries by GDP per Capita" in output
        assert "Top Countries by GDP Growth Rate" in output
        
        # Check that we see the right countries in the right order
        assert "1. Country A: $50,000.00" in output
        assert "2. Country B: $40,000.00" in output
        assert "Country C" not in output  # Should be cut off by top_n=2
        
        assert "1. Country C: 4.50%" in output
        assert "2. Country B: 3.50%" in output
        assert "Country A: 2.50%" not in output  # Should be cut off by top_n=2
    finally:
        sys.stdout = original_stdout


@pytest.mark.asyncio
async def test_main_success() -> None:
    """Test the main function with successful execution."""
    # Create mock objects
    mock_args = MagicMock()
    mock_args.output = "test_output.json"
    mock_args.verbose = False
    mock_args.pretty = False
    mock_args.summary = False
    
    mock_crawler = AsyncMock(spec=WikipediaGDPCrawler)
    
    # Create test data
    per_capita = [
        GDPPerCapita(country="Country A", rank=1, gdp_per_capita=50000.0, year=2023),
    ]
    
    growth_rates = [
        GDPGrowthRate(country="Country B", rank=1, growth_rate_percent=3.5, year=2023),
    ]
    
    mock_data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
    mock_crawler.crawl.return_value = mock_data
    
    with patch("src.cli.parse_args", return_value=mock_args), \
         patch("src.cli.setup_logging") as mock_setup_logging, \
         patch("src.cli.WikipediaGDPCrawler", return_value=mock_crawler), \
         patch("pathlib.Path.mkdir"):
        
        # Run the main function
        result = await main()
        
        # Check that setup_logging was called
        mock_setup_logging.assert_called_once_with(False)
        
        # Check that crawler was initialized and crawl() was called
        mock_crawler.crawl.assert_called_once()
        
        # Check that save_to_json was called
        mock_crawler.save_to_json.assert_called_once()
        
        # Check exit code
        assert result == 0


@pytest.mark.asyncio
async def test_main_with_pretty_json() -> None:
    """Test the main function with pretty JSON option."""
    # Create mock objects
    mock_args = MagicMock()
    mock_args.output = "test_output.json"
    mock_args.verbose = False
    mock_args.pretty = True
    mock_args.summary = False
    
    mock_crawler = AsyncMock(spec=WikipediaGDPCrawler)
    
    # Create test data
    per_capita = [
        GDPPerCapita(country="Country A", rank=1, gdp_per_capita=50000.0, year=2023),
    ]
    
    growth_rates = [
        GDPGrowthRate(country="Country B", rank=1, growth_rate_percent=3.5, year=2023),
    ]
    
    mock_data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
    mock_crawler.crawl.return_value = mock_data
    
    with patch("src.cli.parse_args", return_value=mock_args), \
         patch("src.cli.setup_logging"), \
         patch("src.cli.WikipediaGDPCrawler", return_value=mock_crawler), \
         patch("pathlib.Path.mkdir"), \
         patch("builtins.open", MagicMock()), \
         patch("json.dump") as mock_json_dump:
        
        # Run the main function
        result = await main()
        
        # Check that json.dump was called with indent parameter
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        assert "indent" in kwargs
        assert kwargs["indent"] == 2
        
        # Check exit code
        assert result == 0


@pytest.mark.asyncio
async def test_main_with_summary() -> None:
    """Test the main function with summary option."""
    # Create mock objects
    mock_args = MagicMock()
    mock_args.output = "test_output.json"
    mock_args.verbose = False
    mock_args.pretty = False
    mock_args.summary = True
    mock_args.top = 10
    
    mock_crawler = AsyncMock(spec=WikipediaGDPCrawler)
    
    # Create test data
    per_capita = [
        GDPPerCapita(country="Country A", rank=1, gdp_per_capita=50000.0, year=2023),
    ]
    
    growth_rates = [
        GDPGrowthRate(country="Country B", rank=1, growth_rate_percent=3.5, year=2023),
    ]
    
    mock_data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
    mock_crawler.crawl.return_value = mock_data
    
    with patch("src.cli.parse_args", return_value=mock_args), \
         patch("src.cli.setup_logging"), \
         patch("src.cli.WikipediaGDPCrawler", return_value=mock_crawler), \
         patch("pathlib.Path.mkdir"), \
         patch("src.cli.print_summary") as mock_print_summary:
        
        # Run the main function
        result = await main()
        
        # Check that print_summary was called
        mock_print_summary.assert_called_once_with(mock_data.combined_data, 10)
        
        # Check exit code
        assert result == 0


@pytest.mark.asyncio
async def test_main_with_error() -> None:
    """Test the main function with an error during execution."""
    # Create mock objects that will raise an exception
    mock_args = MagicMock()
    mock_crawler = AsyncMock(spec=WikipediaGDPCrawler)
    mock_crawler.crawl.side_effect = Exception("Test error")
    
    with patch("src.cli.parse_args", return_value=mock_args), \
         patch("src.cli.setup_logging"), \
         patch("src.cli.WikipediaGDPCrawler", return_value=mock_crawler), \
         patch("logging.getLogger") as mock_get_logger:
        
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Run the main function
        result = await main()
        
        # Check that logger.error was called
        mock_logger.error.assert_called_once()
        
        # Check exit code (should be non-zero for error)
        assert result == 1 