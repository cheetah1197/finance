import asyncio
from sqlmodel import create_async_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

# --- IMPORTANT: Replace with your actual database URL ---
# This example uses a placeholder.
DATABASE_URL = "postgresql+asyncpg://user:password@host/dbname"

# --- Import your models and data lists ---
# NOTE: Assume these schemas are defined in your project
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
    
    # Map static data to the Product model fields
    product_values = [
        {'code': p['code'], 'description': p['description'], 'unit_of_measure': p['unit_of_measure']} 
        for p in ALL_HS_PRODUCTS
    ]

    if not product_values:
        print("WARNING: ALL_HS_PRODUCTS list is empty. Skipping product load.")
        return

    # Use PostgreSQL UPSERT for efficiency and idempotence (can run multiple times safely)
    insert_stmt = pg_insert(Product).values(product_values)
    
    # Define the update on conflict (only update description if code exists)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['code'],  # 'code' is the primary key for conflict detection
        set_={'description': insert_stmt.excluded['description'],
              'unit_of_measure': insert_stmt.excluded['unit_of_measure']}
    )
    
    try:
        await session.execute(upsert_stmt)
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
    
    # Define the countries you want to track tariffs for
    target_countries = [
        {'code': 'USA', 'name': 'United States'},
        # Add other reporter countries if needed, e.g., {'code': 'CAN', 'name': 'Canada'}
    ]

    # Use PostgreSQL UPSERT
    country_values = target_countries
    insert_stmt = pg_insert(Country).values(country_values)
    
    # On conflict (if the country code already exists), do nothing
    upsert_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=['code'] 
    )

    try:
        await session.execute(upsert_stmt)
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
    
    print("Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # Step 1: Ensure all tables are created (Optional, but good practice for setup)
        # Note: In a production setup, you would use Alembic migrations instead of this.
        # await conn.run_sync(SQLModel.metadata.create_all) 
        pass 
        
    async with AsyncSession(engine) as session:
        # Run loaders
        await load_countries(session)
        await load_products(session)

    print("\n--- Database Setup Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
