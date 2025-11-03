from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint

class Tariff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Reporter Country (The country imposing the tariff)
    country_id: int = Field(foreign_key="country.id", index=True) 
    
    product_code: str = Field(index=True) # HS 6-digit product code
    
    year: int 
    
    # 1. MFN Simple Average Rate (Applied to countries without a preferential agreement)
    mfn_simple_average_rate: float
    
    # 2. Preferential Simple Average Rate (Applied to countries *with* a preferential agreement)
    # Note: WITS aggregates various preferential rates into one "Preferential Simple Average" indicator.
    pref_simple_average_rate: Optional[float] 
    
    # The Effective Applied Tariff is often the minimum of the two, but WITS also calculates this
    # applied_simple_average_rate: Optional[float] 
    
    __table_args__ = (
        # The unique constraint ensures you only have one record for a given product by a country in a year.
        UniqueConstraint("country_id", "product_code", "year", name="uc_country_product_year"),
    )

class TariffCreate(SQLModel):
    country_id: int
    product_code: str
    year: int
    mfn_simple_average_rate: float
    pref_simple_average_rate: Optional[float]
    
# Schema for READING data (API Output/Response)
class TariffRead(Tariff):
    pass