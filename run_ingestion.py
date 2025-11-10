import asyncio
# Importing the specific async components from SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine 
from sqlmodel.ext.asyncio.session import AsyncSession 

# Import the instantiated settings object for the DB URL
from app.core.config import settings

# Import the core data ingestion logic
from app.services.fetch_wits_tariff_data import fetch_and_save_wits_tariffs

async def run_tariff_ingestion():
    """
    Main function to execute the long-running WITS tariff data ingestion pipeline.
    """
    db_url = settings.DATABASE_URL
    
    if not db_url:
        print("ERROR: DATABASE_URL not found in config. Cannot proceed with ingestion.")
        return

    print("--- Starting WITS Tariff Data Ingestion Process ---")
    
    # 1. Create the asynchronous database engine
    engine = create_async_engine(db_url, echo=False)
    
    try:
        # 2. Open an AsyncSession context
        async with AsyncSession(engine) as session:
            # 3. Call the main fetching function
            await fetch_and_save_wits_tariffs(session)
            
        print("\n--- WITS Tariff Ingestion finished successfully. ---")
        
    except Exception as e:
        print(f"\nFATAL ERROR during ingestion: {e}")

if __name__ == "__main__":
    # Execute this script using: python run_ingestion.py
    asyncio.run(run_tariff_ingestion())
