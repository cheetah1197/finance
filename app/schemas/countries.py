from sqlmodel import Field, SQLModel
from typing import Optional, List
import enum

# Use an Enum for the column type to enforce validity in the DB
class Region(str, enum.Enum):
    EUROPE = "Europe"
    ASIA = "Asia"
    AMERICA = "America"
    AFRICA = "Africa"
    OCEANIA = "OCEANIA"

# Model for the database table
class Country(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True) # e.g., 'DE', 'FR'
    name: str
    region: Region
    
    # You could optionally add a relationship field here (advanced, for later)
    # tariffs: List["Tariff"] = Relationship(back_populates="country")