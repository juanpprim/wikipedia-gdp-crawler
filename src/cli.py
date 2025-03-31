"""Command-line interface for the Wikipedia GDP crawler."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import msgspec

from .crawler import WikipediaGDPCrawler
from .models import CountryStats


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.
    
    Args:
        verbose: Whether to use verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Wikipedia GDP data crawler",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "-o", 
        "--output",
        type=str,
        default="gdp_data.json",
        help="Output file path for the GDP data",
    )
    
    parser.add_argument(
        "-v", 
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Output pretty JSON (readable but larger)",
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of the gathered data",
    )
    
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top countries to show in summary",
    )
    
    return parser.parse_args()


def print_summary(data: Dict[str, CountryStats], top_n: int = 10) -> None:
    """Print a summary of the GDP data.
    
    Args:
        data: Dictionary mapping country names to their GDP stats
        top_n: Number of top countries to display
    """
    # Countries with highest GDP per capita
    print("\n=== Top Countries by GDP per Capita ===")
    countries_by_gdp = sorted(
        [c for c in data.values() if c.gdp_per_capita is not None],
        key=lambda x: x.gdp_per_capita or 0,
        reverse=True,
    )
    
    for i, country in enumerate(countries_by_gdp[:top_n], 1):
        if country.gdp_per_capita is not None:
            print(f"{i}. {country.country}: ${country.gdp_per_capita:,.2f}")
    
    # Countries with highest growth rate
    print("\n=== Top Countries by GDP Growth Rate ===")
    countries_by_growth = sorted(
        [c for c in data.values() if c.gdp_growth_rate is not None],
        key=lambda x: x.gdp_growth_rate or 0,
        reverse=True,
    )
    
    for i, country in enumerate(countries_by_growth[:top_n], 1):
        if country.gdp_growth_rate is not None:
            print(f"{i}. {country.country}: {country.gdp_growth_rate:.2f}%")


async def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    args = parse_args()
    setup_logging(args.verbose)
    
    try:
        logger.info("Starting Wikipedia GDP crawler")
        crawler = WikipediaGDPCrawler()
        data = await crawler.crawl()
        
        output_path = Path(args.output)
        
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.pretty:
            # Convert to Python dict first for pretty printing
            data_dict = msgspec.json.decode(msgspec.json.encode(data))
            with open(output_path, "w") as f:
                json.dump(data_dict, f, indent=2, default=str)
        else:
            crawler.save_to_json(data, str(output_path))
        
        logger.info(f"Data saved to {output_path}")
        
        if args.summary:
            print_summary(data.combined_data, args.top)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def run() -> None:
    """Entry point for the CLI script."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    run() 