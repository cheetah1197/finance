# app/schemas/tariffs.py
from pydantic import BaseModel
from typing import Optional

# Schema for input (e.g., when creating or updating a tariff record)
class TariffBase(BaseModel):
    country_code: str
    product_code: str
    import_duty_rate: float

# Schema for full response (includes an ID, for example)
class Tariff(TariffBase):
    id: int
    description: Optional[str] = None # Optional field

    class Config:
        # This tells Pydantic to support ORM objects if you use SQLAlchemy later
        orm_mode = True