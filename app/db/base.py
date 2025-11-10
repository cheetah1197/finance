from sqlmodel import SQLModel
from app.schemas.countries import Country
from app.schemas.products import Product
from app.schemas.tariffs import Tariff

# Define Base as the central metadata object for Alembic to track
# It should include all your table definitions
Base = SQLModel 
