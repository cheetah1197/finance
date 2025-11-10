import asyncio
import os
import sys
# FIX: create_async_engine is correctly imported from sqlalchemy.ext.asyncio
from sqlalchemy.ext.asyncio import create_async_engine 
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- ASSUMED IMPORTS ---
# You need to ensure these files exist and define the necessary constants/functions.
from app.core.config import settings # Assuming settings.DATABASE_URL exists
from app.services.fetch_wits_tariff_data import fetch_and_save_wits_tariffs
# --- END ASSUMED IMPORTS ---

# --- TEMPLATE FOR ASYNC DB SETUP (Adjust based on your project) ---
# NOTE: Replace 'postgresql+asyncpg' with your actual driver if different
DATABASE_URL = settings.DATABASE_URL # e.g., "postgresql+asyncpg://user:pass@host/db"
engine = create_async_engine(DATABASE_URL, echo=False) 

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional session for the database."""
    async with AsyncSession(engine) as session:
        yield session

# --- MAIN RUNNER ---

async def main():
    """Entry point for the data ingestion script."""
    print("Initializing WITS Ingestion Pipeline...")
    
    # We yield the session once and run the service
    async for session in get_session():
        await fetch_and_save_wits_tariffs(session)

if __name__ == "__main__":
    try:
        # This will block until the ingestion is complete
        asyncio.run(main())
    except ImportError as e:
        print(f"\n[CRITICAL ERROR] Could not import application modules. Check your project structure and paths: {e}")
        print("Required files: core/config.py (with DATABASE_URL), app/services/wits_ingestion.py, etc.")
    except Exception as e:
        print(f"\n[CRITICAL RUNTIME ERROR] Failed to run ingestion: {e}")
