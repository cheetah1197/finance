
# app/schemas/tariffs.py
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint # We fixed this import previously!

# 1. The Core ORM Model (Defines the DB table structure)
class Tariff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key to the Country table
    country_id: int = Field(foreign_key="country.id", index=True) 
    
    product_code: str = Field(index=True)
    import_duty_rate: float
    
    __table_args__ = (
        UniqueConstraint("country_id", "product_code", name="uc_country_product"),
    )

# -----------------------------------------------------------------
# 2. Pydantic Schemas for API Input and Output (ADD THESE TWO CLASSES)
# -----------------------------------------------------------------

# Schema for CREATING data (Client Input)
# We exclude the 'id' because the client shouldn't provide it; the DB generates it.
class TariffCreate(SQLModel):
    country_id: int
    product_code: str
    import_duty_rate: float

# Schema for READING data (API Output/Response)
# This inherits ALL fields from Tariff, including the database-generated 'id'.
class TariffRead(Tariff):
    pass