from typing import Generator, AsyncGenerator
from sqlmodel import SQLModel, Session # Keep Session imported if needed for other sync models/tools
from sqlmodel.ext.asyncio.session import AsyncSession # <-- NEW/CORRECT ASYNC SESSION IMPORT
from sqlalchemy.ext.asyncio import create_async_engine # Import engine from sqlalchemy.ext.asyncio
from app.core.config import settings
from app.schemas.tariffs import Tariff 
from app.schemas.countries import Country 
from app.schemas.products import Product 
from app.schemas.economics import EconomicIndicator

# 1. Create the Async Engine
# The engine itself is fine since it was created with create_async_engine
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True, 
)

# 2. Function to create the database and tables (run once)
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all) 
        await conn.run_sync(SQLModel.metadata.create_all)

# 3. Dependency function to yield an ASYNCHRONOUS database session for each request
async def get_session() -> AsyncGenerator[AsyncSession, None]: # <-- CORRECT TYPE HINT
    # VVV --- USE AsyncSession HERE --- VVV
    async with AsyncSession(engine) as session:
        try:
            yield session
        except Exception:
            # Important for transactions: if an error occurs, rollback.
            await session.rollback()
            raise
        finally:
            # Ensure the session is closed after the request is processed
            await session.close()