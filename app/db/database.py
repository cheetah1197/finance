from typing import Generator, AsyncGenerator
from sqlmodel import SQLModel, Session
from sqlalchemy.ext.asyncio import create_async_engine # Import engine from sqlalchemy.ext.asyncio
from app.core.config import settings
from app.schemas.tariffs import Tariff 
from app.schemas.countries import Country 
from app.schemas.products import Product 

# 1. Create the Async Engine
# echo=True prints the SQL queries to the console, which is helpful for learning!
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True, 
    
)

# 2. Function to create the database and tables (run once)
async def create_db_and_tables():
    async with engine.begin() as conn:
        # This drops tables first (useful for development/testing) and then creates them
        await conn.run_sync(SQLModel.metadata.drop_all) 
        await conn.run_sync(SQLModel.metadata.create_all)

# 3. Dependency function to yield a database session for each request
async def get_session() -> AsyncGenerator[Session, None]:
    async with Session(engine) as session:
        try:
            yield session
        finally:
            await session.close()