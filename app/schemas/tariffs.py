from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint

class Tariff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Reporter Country ID (Foreign Key to country.id)
    country_id: int = Field(foreign_key="country.id", index=True) 
    
    # Product Code (Foreign Key to product.code, max_length for efficiency)
    product_code: str = Field(foreign_key="product.code", index=True, max_length=6) 
    
    year: int 
    
    # 1. MFN Simple Average Rate (WITS Indicator: PMF)
    # Changed to Optional[float] to handle cases where MFN data is not available.
    mfn_simple_average_rate: Optional[float] 
    
    # 2. Preferential Simple Average Rate (WITS Indicator: PRFP)
    pref_simple_average_rate: Optional[float] 
    
    # 3. Applied Simple Average Rate (WITS Indicator: ATF)
    applied_simple_average_rate: Optional[float] 
    
    __table_args__ = (
        # Ensures unique entry per country, product, and year.
        UniqueConstraint("country_id", "product_code", "year", name="uc_country_product_year"),
        {'extend_existing': True}
    )

class TariffCreate(SQLModel):
    country_id: int
    product_code: str
    year: int
    mfn_simple_average_rate: Optional[float]
    pref_simple_average_rate: Optional[float]
    applied_simple_average_rate: Optional[float] # Added ATF to the creation schema
    
# Schema for READING data (API Output/Response)
class TariffRead(Tariff):
    pass