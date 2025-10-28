# app/schemas/economics.py
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import date
from sqlalchemy import UniqueConstraint

# 1. The combined ORM Model and Pydantic Schema for the DB table
class EconomicIndicator(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key to the Country table (using the country model you defined)
    country_id: int = Field(foreign_key="country.id", index=True) 
    
    indicator_code: str = Field(index=True)  # e.g., 'GDP', 'INFLATION', 'UNEMPLOYMENT'
    date: date # Use the date type for tracking data over time
    value: float # The actual economic value (e.g., 2.5 for 2.5%)

    # Add a unique constraint to prevent duplicate entries for the same indicator/country/date
    __table_args__ = (
        UniqueConstraint("country_id", "indicator_code", "date", name="uc_econ_data"),
    )

# 2. Pydantic Schemas for API Operations
class EconomicIndicatorCreate(SQLModel):
    country_id: int
    indicator_code: str
    date: date
    value: float

class EconomicIndicatorRead(EconomicIndicator):
    pass