# app/services/data_loader.py
import httpx
import asyncio
from sqlmodel import Session, select
from app.db.database import engine
from app.schemas.countries import Country
from app.schemas.tariffs import TariffCreate
from app.schemas.economics import EconomicIndicatorCreate
from datetime import date
from typing import List

# NOTE: You need to replace this with the actual URL of your data source!
TARIFF_API_URL = "http://example.com/api/tariffs" 

async def fetch_and_load_tariffs(country_code: str, session: Session):
    """Fetches tariff data for a single country and loads it into the database."""
    # 1. Look up the country's database ID
    country_record = await session.exec(
        select(Country).where(Country.code == country_code)
    )
    country = country_record.first()
    if not country:
        print(f"Skipping {country_code}: not found in DB.")
        return

    # 2. Asynchronously fetch data
    async with httpx.AsyncClient() as client:
        # Modify this request based on your actual data source API/structure
        response = await client.get(f"{TARIFF_API_URL}?country={country_code}")
        response.raise_for_status() # Raise exception for bad status codes
        raw_tariffs = response.json()

    # 3. Process and Insert Data
    tariffs_to_insert = []
    for item in raw_tariffs:
        try:
            # Map raw data to the TariffCreate schema
            tariff_data = TariffCreate(
                country_id=country.id, # Use the foreign key ID
                product_code=item.get("HSCode"), # Adjust field names as needed
                import_duty_rate=float(item.get("Rate"))
            )
            # Note: You would add checks here to prevent duplicates before adding to DB
            tariffs_to_insert.append(tariff_data)
        except Exception as e:
            print(f"Error processing tariff for {country_code}: {e}")

    # 4. Save to Database
    # For simplicity, we commit all data at once (you may optimize this later)
    for tariff_data in tariffs_to_insert:
        session.add(tariff_data)

    print(f"Loaded {len(tariffs_to_insert)} tariffs for {country_code}")


async def run_full_data_load():
    """Main function to iterate over all countries and load data."""
    async with engine.begin() as conn:
        # 1. Get all country codes from the DB
        result = await conn.execute(select(Country.code))
        country_codes = result.scalars().all()

        # 2. Use a list of tasks for concurrent fetching
        tasks = []
        async with Session(conn) as session:
            for code in country_codes:
                # Create a task for each country to fetch data concurrently
                tasks.append(fetch_and_load_tariffs(code, session))

            # Run all fetching tasks concurrently
            await asyncio.gather(*tasks) 
            await session.commit()
            print("All data loading tasks completed.")

if __name__ == "__main__":
    asyncio.run(run_full_data_load())