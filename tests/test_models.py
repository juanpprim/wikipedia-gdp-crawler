"""Tests for the data models."""

import datetime
from typing import Dict

import msgspec
import pytest

from src.models import (
    CountryStats,
    GDPGrowthRate,
    GDPPerCapita,
    WikipediaGDPData,
)


def test_gdp_per_capita_model() -> None:
    """Test the GDPPerCapita model."""
    data = GDPPerCapita(
        country="Test Country",
        rank=1,
        gdp_per_capita=50000.0,
        year=2023,
    )
    
    assert data.country == "Test Country"
    assert data.rank == 1
    assert data.gdp_per_capita == 50000.0
    assert data.year == 2023
    assert data.source == "IMF"  # Default value
    assert data.note is None  # Default value


def test_gdp_growth_rate_model() -> None:
    """Test the GDPGrowthRate model."""
    data = GDPGrowthRate(
        country="Test Country",
        rank=2,
        growth_rate_percent=3.5,
        year=2023,
        note="Test note",
    )
    
    assert data.country == "Test Country"
    assert data.rank == 2
    assert data.growth_rate_percent == 3.5
    assert data.year == 2023
    assert data.source == "IMF"  # Default value
    assert data.note == "Test note"


def test_country_stats_model() -> None:
    """Test the CountryStats model."""
    today = datetime.date.today()
    data = CountryStats(
        country="Test Country",
        gdp_per_capita=50000.0,
        gdp_per_capita_rank=1,
        gdp_growth_rate=3.5,
        gdp_growth_rate_rank=2,
    )
    
    assert data.country == "Test Country"
    assert data.gdp_per_capita == 50000.0
    assert data.gdp_per_capita_rank == 1
    assert data.gdp_growth_rate == 3.5
    assert data.gdp_growth_rate_rank == 2
    assert isinstance(data.last_updated, datetime.date)
    assert (today - data.last_updated).days <= 1  # Should be today


def test_wikipedia_gdp_data_model() -> None:
    """Test the WikipediaGDPData model."""
    per_capita = [
        GDPPerCapita(country="Country A", rank=1, gdp_per_capita=60000.0, year=2023),
        GDPPerCapita(country="Country B", rank=2, gdp_per_capita=50000.0, year=2023),
    ]
    
    growth_rates = [
        GDPGrowthRate(country="Country A", rank=2, growth_rate_percent=3.0, year=2023),
        GDPGrowthRate(country="Country C", rank=1, growth_rate_percent=4.0, year=2023),
    ]
    
    data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
    
    assert len(data.per_capita) == 2
    assert len(data.growth_rates) == 2
    assert len(data.combined_data) == 0  # Empty before combine_data is called


def test_combine_data() -> None:
    """Test the combine_data method."""
    per_capita = [
        GDPPerCapita(country="Country A", rank=1, gdp_per_capita=60000.0, year=2023),
        GDPPerCapita(country="Country B", rank=2, gdp_per_capita=50000.0, year=2023),
    ]
    
    growth_rates = [
        GDPGrowthRate(country="Country A", rank=2, growth_rate_percent=3.0, year=2023),
        GDPGrowthRate(country="Country C", rank=1, growth_rate_percent=4.0, year=2023),
    ]
    
    data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
    data.combine_data()
    
    assert len(data.combined_data) == 3  # Country A, B, and C
    
    # Check Country A with both data points
    country_a = data.combined_data["Country A"]
    assert country_a.country == "Country A"
    assert country_a.gdp_per_capita == 60000.0
    assert country_a.gdp_per_capita_rank == 1
    assert country_a.gdp_growth_rate == 3.0
    assert country_a.gdp_growth_rate_rank == 2
    
    # Check Country B with only per-capita data
    country_b = data.combined_data["Country B"]
    assert country_b.country == "Country B"
    assert country_b.gdp_per_capita == 50000.0
    assert country_b.gdp_per_capita_rank == 2
    assert country_b.gdp_growth_rate is None
    assert country_b.gdp_growth_rate_rank is None
    
    # Check Country C with only growth rate data
    country_c = data.combined_data["Country C"]
    assert country_c.country == "Country C"
    assert country_c.gdp_per_capita is None
    assert country_c.gdp_per_capita_rank is None
    assert country_c.gdp_growth_rate == 4.0
    assert country_c.gdp_growth_rate_rank == 1


def test_msgspec_serialization() -> None:
    """Test msgspec serialization of the models."""
    # Create test data
    per_capita = [
        GDPPerCapita(country="Country A", rank=1, gdp_per_capita=60000.0, year=2023),
    ]
    
    growth_rates = [
        GDPGrowthRate(country="Country A", rank=2, growth_rate_percent=3.0, year=2023),
    ]
    
    data = WikipediaGDPData(per_capita=per_capita, growth_rates=growth_rates)
    data.combine_data()
    
    # Test serialization
    json_bytes = msgspec.json.encode(data)
    assert isinstance(json_bytes, bytes)
    
    # Test deserialization
    decoded_data = msgspec.json.decode(json_bytes, type=WikipediaGDPData)
    assert isinstance(decoded_data, WikipediaGDPData)
    assert len(decoded_data.per_capita) == 1
    assert len(decoded_data.growth_rates) == 1
    assert decoded_data.per_capita[0].country == "Country A"
    assert decoded_data.growth_rates[0].country == "Country A" 