import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select
# FIX: Import the async engine directly from SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine 
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Import configuration and models
from app.core.config import settings
from app.schemas.countries import Country
from app.schemas.products import Product 
from app.data.product_list import ALL_HS_PRODUCTS 

# ----------------------------------------------------------------------
# 1. Product Loading Logic
# ----------------------------------------------------------------------

async def load_products(session: AsyncSession):
    """
    Performs a bulk UPSERT of all HS products from the static list.
    """
    print("\n--- Starting Product Data Load ---")
    
    product_values = [
        # FIX: ONLY include 'code' and 'description' as these are the only fields available.
        {'code': p['code'], 'description': p['description']} 
        for p in ALL_HS_PRODUCTS
    ]

    if not product_values:
        print("WARNING: ALL_HS_PRODUCTS list is empty. Skipping product load.")
        return

    insert_stmt = pg_insert(Product).values(product_values)
    
    # FIX: Update the UPSERT SET clause to only update 'description'
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['code'], 
        set_={'description': insert_stmt.excluded['description']}
    )
    
    try:
        await session.exec(upsert_stmt)
        await session.commit()
        print(f"Successfully loaded/updated {len(product_values)} products.")
    except Exception as e:
        await session.rollback()
        print(f"ERROR loading products: {e}")

# ----------------------------------------------------------------------
# 2. Country Loading Logic
# ----------------------------------------------------------------------

async def load_countries(session: AsyncSession):
    """
    Inserts necessary country codes (e.g., USA) if they don't exist.
    """
    print("\n--- Starting Country Data Load ---")
    
    target_countries = [
        # FIX: Set the region to the exact string value expected by the Region Enum
        {'code': 'USA', 'name': 'United States', 'region': 'America'},
    ]

    country_values = target_countries
    insert_stmt = pg_insert(Country).values(country_values)
    
    # On conflict (country code exists), do nothing
    upsert_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=['code'] 
    )

    try:
        await session.exec(upsert_stmt)
        await session.commit()
        print(f"Successfully ensured {len(country_values)} target countries are present.")
    except Exception as e:
        await session.rollback()
        print(f"ERROR loading countries: {e}")
        
# ----------------------------------------------------------------------
# 3. Main Execution Function
# ----------------------------------------------------------------------

async def main():
    """Initializes the database connection and runs the setup loaders."""
    db_url = settings.DATABASE_URL
    
    if not db_url:
        print("ERROR: DATABASE_URL not found in config. Cannot connect.")
        return
    
    print("Connecting to database...")
    # FIX: Using the directly imported create_async_engine
    engine = create_async_engine(db_url, echo=False)
    
    async with AsyncSession(engine) as session:
        await load_countries(session)
        await load_products(session)

    print("\n--- Database Setup Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
