"""Tests for the Wikipedia parser."""

import pytest

from src.parser import WikipediaParser


# Sample HTML data for testing
GDP_PER_CAPITA_HTML = """
<h2>List of countries by GDP (nominal) per capita</h2>
<table class="wikitable sortable">
<tr>
<th>Rank</th>
<th>Country/Territory</th>
<th>GDP per capita (US$)</th>
</tr>
<tr>
<td>1</td>
<td>Luxembourg</td>
<td>128,572</td>
</tr>
<tr>
<td>2</td>
<td>Ireland</td>
<td>94,392</td>
</tr>
<tr>
<td>3</td>
<td>Switzerland[a]</td>
<td>84,658</td>
</tr>
</table>
"""

GDP_GROWTH_RATE_HTML = """
<h2>List of countries by real GDP growth rate</h2>
<table class="wikitable sortable">
<tr>
<th>Rank</th>
<th>Country/Territory</th>
<th>Real GDP growth rate (%)</th>
</tr>
<tr>
<td>1</td>
<td>Guyana</td>
<td>62.3</td>
</tr>
<tr>
<td>2</td>
<td>Libya[a]</td>
<td>17.9</td>
</tr>
<tr>
<td>3</td>
<td>Macao</td>
<td>17.2</td>
</tr>
</table>
"""


def test_init() -> None:
    """Test parser initialization."""
    parser = WikipediaParser()
    assert parser.current_year == 2023


def test_clean_country_name() -> None:
    """Test country name cleaning."""
    parser = WikipediaParser()
    
    # Test removing footnotes
    assert parser._clean_country_name("Switzerland[a]") == "Switzerland"
    
    # Test removing HTML tags
    assert parser._clean_country_name("<b>Switzerland</b>") == "Switzerland"
    
    # Test removing extra whitespace
    assert parser._clean_country_name("  Switzerland  ") == "Switzerland"
    
    # Test complex case
    assert parser._clean_country_name("  <i>Switzerland</i>[1]  ") == "Switzerland"


def test_parse_float() -> None:
    """Test floating point value parsing."""
    parser = WikipediaParser()
    
    # Test simple number
    assert parser._parse_float("123.45") == 123.45
    
    # Test number with commas
    assert parser._parse_float("123,456.78") == 123456.78
    
    # Test percentage
    assert parser._parse_float("5.4%") == 5.4
    
    # Test invalid input
    assert parser._parse_float("N/A") == 0.0


def test_extract_year_from_html() -> None:
    """Test year extraction from HTML."""
    parser = WikipediaParser()
    
    # Test with a specific year in the HTML
    html = "<h2>GDP per capita (2022)</h2>"
    assert parser._extract_year_from_html(html) == 2022
    
    # Test with no year found (should return default)
    html = "<h2>Some other content</h2>"
    assert parser._extract_year_from_html(html) == 2023


def test_parse_gdp_per_capita() -> None:
    """Test parsing GDP per capita data."""
    parser = WikipediaParser()
    results = parser.parse_gdp_per_capita(GDP_PER_CAPITA_HTML)
    
    assert len(results) == 3
    
    # Check first entry
    assert results[0].country == "Luxembourg"
    assert results[0].rank == 1
    assert results[0].gdp_per_capita == 128572
    
    # Check second entry
    assert results[1].country == "Ireland"
    assert results[1].rank == 2
    assert results[1].gdp_per_capita == 94392
    
    # Check third entry (with footnote)
    assert results[2].country == "Switzerland"  # Note: footnote should be removed
    assert results[2].rank == 3
    assert results[2].gdp_per_capita == 84658


def test_parse_gdp_growth_rate() -> None:
    """Test parsing GDP growth rate data."""
    parser = WikipediaParser()
    results = parser.parse_gdp_growth_rate(GDP_GROWTH_RATE_HTML)
    
    assert len(results) == 3
    
    # Check first entry
    assert results[0].country == "Guyana"
    assert results[0].rank == 1
    assert results[0].growth_rate_percent == 62.3
    
    # Check second entry (with footnote)
    assert results[1].country == "Libya"  # Note: footnote should be removed
    assert results[1].rank == 2
    assert results[1].growth_rate_percent == 17.9
    
    # Check third entry
    assert results[2].country == "Macao"
    assert results[2].rank == 3
    assert results[2].growth_rate_percent == 17.2


def test_empty_html() -> None:
    """Test parsing empty HTML."""
    parser = WikipediaParser()
    
    # Test empty HTML for GDP per capita
    results = parser.parse_gdp_per_capita("")
    assert len(results) == 0
    
    # Test empty HTML for GDP growth rate
    results = parser.parse_gdp_growth_rate("")
    assert len(results) == 0


def test_malformed_html() -> None:
    """Test parsing malformed HTML."""
    parser = WikipediaParser()
    
    # Test malformed HTML (no rows)
    malformed_html = "<table class='wikitable'></table>"
    results = parser.parse_gdp_per_capita(malformed_html)
    assert len(results) == 0
    
    # Test malformed HTML (empty rows)
    malformed_html = "<table class='wikitable'><tr></tr><tr></tr></table>"
    results = parser.parse_gdp_growth_rate(malformed_html)
    assert len(results) == 0 