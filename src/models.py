"""Data models for GDP information."""

from datetime import date
from typing import Dict, List, Optional, Union

import msgspec


class GDPPerCapita(msgspec.Struct):
    """Model for GDP per capita data."""

    country: str
    rank: int
    gdp_per_capita: float
    year: int
    source: str = "IMF"
    note: Optional[str] = None


class GDPGrowthRate(msgspec.Struct):
    """Model for GDP growth rate data."""

    country: str
    rank: int
    growth_rate_percent: float
    year: int
    source: str = "IMF"
    note: Optional[str] = None


class CountryStats(msgspec.Struct):
    """Combined GDP statistics for a country."""

    country: str
    gdp_per_capita: Optional[float] = None
    gdp_per_capita_rank: Optional[int] = None
    gdp_growth_rate: Optional[float] = None
    gdp_growth_rate_rank: Optional[int] = None
    last_updated: date = msgspec.field(default_factory=date.today)


class WikipediaGDPData(msgspec.Struct):
    """Container for all extracted GDP data."""

    per_capita: List[GDPPerCapita]
    growth_rates: List[GDPGrowthRate]
    extraction_date: date = msgspec.field(default_factory=date.today)
    combined_data: Dict[str, CountryStats] = msgspec.field(default_factory=dict)

    def combine_data(self) -> None:
        """Combine per-capita and growth rate data into unified country stats."""
        countries: Dict[str, CountryStats] = {}
        
        for entry in self.per_capita:
            if entry.country not in countries:
                countries[entry.country] = CountryStats(country=entry.country)
            countries[entry.country].gdp_per_capita = entry.gdp_per_capita
            countries[entry.country].gdp_per_capita_rank = entry.rank
        
        for entry in self.growth_rates:
            if entry.country not in countries:
                countries[entry.country] = CountryStats(country=entry.country)
            countries[entry.country].gdp_growth_rate = entry.growth_rate_percent
            countries[entry.country].gdp_growth_rate_rank = entry.rank
        
        self.combined_data = countries 