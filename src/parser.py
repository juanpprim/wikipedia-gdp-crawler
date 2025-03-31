"""Module for parsing Wikipedia HTML pages to extract GDP data."""

import re
import logging
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from .models import GDPGrowthRate, GDPPerCapita


logger = logging.getLogger(__name__)


class WikipediaParser:
    """Parser for extracting GDP data from Wikipedia pages."""

    def __init__(self) -> None:
        """Initialize the Wikipedia parser."""
        self.current_year = 2023  # Default year, can be updated based on page content

    def _clean_country_name(self, name: str) -> str:
        """Clean a country name by removing footnotes and extra spaces."""
        # Remove footnotes like [a] or [1]
        name = re.sub(r'\[\w+\]', '', name)
        # Remove any HTML tags
        name = re.sub(r'<[^>]+>', '', name)
        # Clean up extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def _parse_float(self, value: str) -> float:
        """Parse a string into a float, handling common formatting."""
        # Remove commas, percentage signs, and other non-numeric characters
        cleaned_value = re.sub(r'[^\d.\-+]', '', value)
        try:
            return float(cleaned_value)
        except ValueError:
            logger.warning(f"Failed to parse float from: '{value}', cleaned to: '{cleaned_value}'")
            return 0.0

    def _extract_year_from_html(self, html: str) -> int:
        """Extract the year from the HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for year patterns in the table headers or title
        year_text = soup.find('title')
        if year_text:
            logger.info(f"Title text: {year_text.text}")
            year_match = re.search(r'(\d{4})', year_text.text)
            if year_match:
                return int(year_match.group(1))
                
        # Try to find year in the main content or headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings:
            year_match = re.search(r'(\d{4})', heading.text)
            if year_match:
                return int(year_match.group(1))
                
        return self.current_year

    def parse_gdp_per_capita(self, html: str) -> List[GDPPerCapita]:
        """Parse GDP per capita data from Wikipedia HTML."""
        results: List[GDPPerCapita] = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract the year from the HTML content
        year = self._extract_year_from_html(html)
        logger.info(f"Extracted year: {year}")
        
        # Find all tables
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables total")
        
        # Find wikitables specifically
        wikitables = soup.find_all('table', class_='wikitable')
        logger.info(f"Found {len(wikitables)} wikitables")
        
        # Check both regular tables and wikitables
        for i, table in enumerate(tables):
            header_row = table.find('tr')
            if not header_row:
                continue
                
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            logger.info(f"Table {i+1} headers: {headers}")
            
            # Focus on tables with country/territory column
            if any('country' in header.lower() for header in headers):
                logger.info(f"Found potential GDP table with headers: {headers}")
                
                # Process each data row
                rows = table.find_all('tr')[1:]  # Skip header row
                logger.info(f"Found {len(rows)} data rows")
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 2:
                        continue
                        
                    try:
                        # Assuming first column is country/territory and second column is GDP value
                        # Find the country index (usually first or second column)
                        country_index = next((i for i, h in enumerate(headers) if 'country' in h.lower()), 0)
                        country_element = cells[country_index] if country_index < len(cells) else cells[0]
                        country = self._clean_country_name(country_element.get_text(strip=True))
                        
                        # Find GDP value (often in columns following country)
                        gdp_index = 1 if country_index == 0 else 2
                        rank = 0
                        
                        # If the first column is a number, it's likely the rank
                        if country_index > 0 and re.match(r'^\d+$', cells[0].get_text(strip=True)):
                            rank = int(cells[0].get_text(strip=True))
                        
                        # Try to get GDP value
                        if gdp_index < len(cells):
                            gdp_text = cells[gdp_index].get_text(strip=True)
                            gdp_value = self._parse_float(gdp_text)
                            
                            logger.info(f"Found entry: {country}, rank: {rank}, GDP: {gdp_value}")
                            
                            if country and gdp_value > 0:
                                results.append(
                                    GDPPerCapita(
                                        country=country,
                                        rank=rank,
                                        gdp_per_capita=gdp_value,
                                        year=year
                                    )
                                )
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Error processing row: {e}")
                        continue
                
                # If we found data in this table, we can stop
                if results:
                    break
        
        return results

    def parse_gdp_growth_rate(self, html: str) -> List[GDPGrowthRate]:
        """Parse GDP growth rate data from Wikipedia HTML."""
        results: List[GDPGrowthRate] = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Log page title
        title = soup.find('title')
        logger.info(f"Growth rate page title: {title.text if title else 'No title found'}")
        
        # Extract year information
        year = self.current_year
        year_elements = soup.find_all(string=re.compile(r'\d{4}'))
        for elem in year_elements:
            if 'GDP' in elem or 'growth' in elem.lower():
                year_match = re.search(r'(\d{4})', elem)
                if year_match:
                    year = int(year_match.group(1))
                    logger.info(f"Found growth rate year: {year}")
                    break
        
        logger.info(f"Using growth rate year: {year}")
        
        # Find all tables
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables total in growth rate page")
        
        # Find wikitables specifically
        wikitables = soup.find_all('table', class_='wikitable')
        logger.info(f"Found {len(wikitables)} wikitables in growth rate page")
        
        # Check both regular tables and wikitables
        for i, table in enumerate(tables):
            header_row = table.find('tr')
            if not header_row:
                continue
                
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            logger.info(f"Growth rate table {i+1} headers: {headers}")
            
            # Focus on tables with country column and growth/rate terminology
            if any('country' in header.lower() for header in headers):
                logger.info(f"Found potential growth rate table with headers: {headers}")
                
                # Process each data row
                rows = table.find_all('tr')[1:]  # Skip header row
                logger.info(f"Found {len(rows)} growth rate data rows")
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 2:
                        continue
                        
                    try:
                        # Assuming first column is rank, second is country/territory, third is growth rate
                        # Find the country index
                        country_index = next((i for i, h in enumerate(headers) if 'country' in h.lower()), 1)
                        country_element = cells[country_index] if country_index < len(cells) else cells[1]
                        country = self._clean_country_name(country_element.get_text(strip=True))
                        
                        # Find rank (often the first column)
                        rank = 0
                        rank_index = 0
                        if rank_index < len(cells) and re.match(r'^\d+$', cells[rank_index].get_text(strip=True)):
                            rank = int(cells[rank_index].get_text(strip=True))
                        
                        # Find growth rate (often third column)
                        growth_index = country_index + 1
                        if growth_index < len(cells):
                            growth_text = cells[growth_index].get_text(strip=True)
                            growth_rate = self._parse_float(growth_text)
                            
                            logger.info(f"Found growth entry: {country}, rank: {rank}, growth: {growth_rate}")
                            
                            if country:
                                results.append(
                                    GDPGrowthRate(
                                        country=country,
                                        rank=rank,
                                        growth_rate_percent=growth_rate,
                                        year=year
                                    )
                                )
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Error processing growth row: {e}")
                        continue
                
                # If we found data in this table, we can stop
                if results:
                    break
        
        return results 