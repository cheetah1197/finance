from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from typing import List, Dict, Any

# Assuming Country and EconomicIndicator are imported/available here, 
# or you can import them from their current locations if they are not in this file.

# A Pydantic model for a single indicator point (e.g., GDP for 2024)
class IndicatorDataPoint(SQLModel):
    indicator_code: str
    date: date
    value: float
    
# The main response structure for a single country
class CountryEconomicResponse(SQLModel):
    country_code: str
    country_name: str
    # This dictionary holds all indicators, grouped by their code
    data: List[IndicatorDataPoint]