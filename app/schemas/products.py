from sqlmodel import Field, SQLModel
from typing import Optional

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=6, primary_key=True)
    description: str # e.g., 'Wheat and meslin'
    unit_of_measure: str = Field(default='N/A')