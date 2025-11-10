import asyncio
from sqlmodel import SQLModel, create_engine
from app.core.config import settings
import re

# Import all models so SQLAlchemy knows about them.
# Ensure these imports match your actual file structure (e.g., app.schemas.countries)
from app.schemas.countries import Country 
from app.schemas.products import Product   
from app.schemas.tariffs import Tariff     

def init_db():
    """
    Initializes the database engine and creates all tables.
    
    CRITICAL FIX: Since the main app uses an async driver (like +asyncpg), 
    we must strip the async part for the synchronous create_engine call.
    """
    db_url = settings.DATABASE_URL
    
    if not db_url:
        print("ERROR: DATABASE_URL not found in config. Cannot proceed.")
        return

    # 1. Strip the async portion (e.g., '+asyncpg') from the URL
    # This forces the synchronous engine to use the standard psycopg2 driver.
    sync_db_url = re.sub(r"\+(\w+)", "", db_url, 1)

    # 2. Use a synchronous engine for this one-time script
    engine = create_engine(sync_db_url, echo=False) 

    print("Attempting to create all tables (Country, Product, Tariff) from schemas...")
    
    # This command reads all classes inheriting from SQLModel and creates
    # the corresponding tables in the database.
    SQLModel.metadata.create_all(engine)
    
    print("Database tables created successfully using the latest schemas.")

if __name__ == "__main__":
    init_db()
