# app/schemas/tariffs.py
from typing import Optional
from sqlmodel import Field, SQLModel # Import Field and SQLModel
from sqlalchemy import UniqueConstraint

# Model for the database table
class Tariff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key to the Country table
    country_id: int = Field(foreign_key="country.id", index=True) 
    
    product_code: str = Field(index=True)
    import_duty_rate: float
    
    # Add a UNIQUE constraint on the combination of columns: 
    # A country should only have ONE rate for a specific product code.
    __table_args__ = (
        UniqueConstraint("country_id", "product_code", name="uc_country_product"),
    )