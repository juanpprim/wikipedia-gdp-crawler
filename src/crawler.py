"""Wikipedia crawler module for fetching GDP data."""

import asyncio
import logging
from typing import Dict, Optional

import httpx
import msgspec

from src.models import WikipediaGDPData
from src.parser import WikipediaParser

logger = logging.getLogger(__name__)


class WikipediaGDPCrawler:
    """Crawler for extracting GDP data from Wikipedia."""

    def __init__(self) -> None:
        """Initialize the Wikipedia crawler."""
        self.parser = WikipediaParser()
        self.gdp_per_capita_url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)_per_capita"
        self.gdp_growth_rate_url = "https://en.wikipedia.org/wiki/List_of_countries_by_real_GDP_growth_rate"
        self.timeout = 30.0  # Timeout in seconds
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.114 Safari/537.36"
        )

    async def fetch_page(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        """Fetch a Wikipedia page.
        
        Args:
            url: URL to fetch
            client: httpx AsyncClient instance
            
        Returns:
            HTML content of the page or None if an error occurred
        """
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    async def crawl(self) -> WikipediaGDPData:
        """Crawl Wikipedia to extract GDP data.
        
        Returns:
            WikipediaGDPData object containing the extracted data
        """
        headers = {"User-Agent": self.user_agent}
        
        async with httpx.AsyncClient(headers=headers) as client:
            # Fetch both pages concurrently
            per_capita_html, growth_rate_html = await asyncio.gather(
                self.fetch_page(self.gdp_per_capita_url, client),
                self.fetch_page(self.gdp_growth_rate_url, client),
            )
            
            # Parse the data
            per_capita_data = []
            growth_rate_data = []
            
            if per_capita_html:
                per_capita_data = self.parser.parse_gdp_per_capita(per_capita_html)
                logger.info(f"Extracted {len(per_capita_data)} GDP per capita entries")
            else:
                logger.warning("Failed to fetch GDP per capita data")
            
            if growth_rate_html:
                growth_rate_data = self.parser.parse_gdp_growth_rate(growth_rate_html)
                logger.info(f"Extracted {len(growth_rate_data)} GDP growth rate entries")
            else:
                logger.warning("Failed to fetch GDP growth rate data")
            
            # Create the result object
            result = WikipediaGDPData(
                per_capita=per_capita_data,
                growth_rates=growth_rate_data,
            )
            
            # Combine the data
            result.combine_data()
            
            return result

    def save_to_json(self, data: WikipediaGDPData, filename: str = "gdp_data.json") -> None:
        """Save the GDP data to a JSON file.
        
        Args:
            data: WikipediaGDPData object
            filename: Path to save the JSON file
        """
        try:
            # Use msgspec for high-performance JSON encoding
            json_bytes = msgspec.json.encode(data)
            with open(filename, "wb") as f:
                f.write(json_bytes)
            logger.info(f"Saved GDP data to {filename}")
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")


async def main() -> None:
    """Main entry point for the crawler."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    crawler = WikipediaGDPCrawler()
    data = await crawler.crawl()
    
    logger.info(f"Found {len(data.per_capita)} GDP per capita entries")
    logger.info(f"Found {len(data.growth_rates)} GDP growth rate entries")
    logger.info(f"Combined data for {len(data.combined_data)} countries")
    
    crawler.save_to_json(data)


if __name__ == "__main__":
    asyncio.run(main()) 