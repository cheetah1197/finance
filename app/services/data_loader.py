# app/services/data_loader.py
import httpx
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session, select
from app.db.database import engine
from app.schemas.countries import Country
from app.schemas.tariffs import TariffCreate
from app.schemas.economics import EconomicIndicatorCreate, EconomicIndicator
from datetime import date
from typing import List

# NOTE: You need to replace this with the actual URL of your data source!
TARIFF_API_URL = "http://example.com/api/tariffs" 

# --- New Constants for World Bank ---
WB_BASE_URL = "https://api.worldbank.org/v2/country"
# Define the specific indicators you want to pull
TARGET_INDICATORS = {
    "GDP_CURRENT": "NY.GDP.MKTP.CD",  # Example: GDP (current US$)
    "INFLATION_CPI": "FP.CPI.TOTL.ZG" # Example: Inflation (CPI)
}

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
            

### WORLD BANK API functions 
async def fetch_worldbank_data(client: httpx.AsyncClient, country_code: str, indicator_id: str, date_range: str) -> list:
    """Fetches ALL pages of data for a specific country and indicator."""
    all_records = []
    page = 1
    total_pages = 1 # Start with 1 page assumed

    while page <= total_pages:
        # Construct the URL for the specific country, indicator, and page number
        url = f"{WB_BASE_URL}/{country_code}/indicator/{indicator_id}?format=json&date={date_range}&page={page}"
        
        try:
            response = await client.get(url)
            response.raise_for_status()
            response_data = response.json()

            if not response_data or len(response_data) < 2:
                # API returned no data or only metadata
                break 

            metadata = response_data[0]
            data_page = response_data[1]
            
            total_pages = metadata.get('pages', 1)
            
            if data_page:
                all_records.extend(data_page)
            
            page += 1
            # Add a small delay to respect API rate limits, especially for large country lists
            await asyncio.sleep(0.1) 

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error fetching {country_code} for {indicator_id}: {e.response.status_code}")
            break
        except Exception as e:
            print(f"General error fetching data for {country_code}: {e}")
            break
            
    return all_records

async def load_all_economic_data(session: AsyncSession):
    """Top-level function to orchestrate the World Bank data load."""
    print("--- Starting World Bank Economic Data Load ---")

    # Get country codes first
    country_codes_result = await session.exec(select(Country.code))
    country_codes = country_codes_result.all()

    DATE_RANGE = "2020:2024" 
    tasks = []

    # Session is now passed in, so we can use it directly
    async with httpx.AsyncClient(timeout=30.0) as client: 
        for country_code in country_codes:
            for indicator_name, indicator_id in TARGET_INDICATORS.items():
                task = _process_and_insert_indicator(
                    client=client, 
                    session=session, # Pass the session down
                    country_code=country_code, 
                    indicator_id=indicator_id, 
                    indicator_name=indicator_name, 
                    date_range=DATE_RANGE
                )
                tasks.append(task)

        # 1. Wait for all concurrent API calls and session.add() operations to finish
        await asyncio.gather(*tasks)

        # 2. COMMIT ALL CHANGES AT ONCE
        # This is the single, required commit for the entire concurrent operation.
        await session.commit()
        # Ensure you also REMOVED 'await session.commit()' from the worker function _process_and_insert_indicator
        
    print("--- World Bank economic data load FINISHED ---")

async def _process_and_insert_indicator(client: httpx.AsyncClient, session: AsyncSession, country_code: str, indicator_id: str, indicator_name: str, date_range: str):
    """Helper to fetch, transform, and insert data for one indicator/country pair."""
    
    raw_data = await fetch_worldbank_data(client, country_code, indicator_id, date_range)
    
    country_obj = await session.exec(select(Country).where(Country.code == country_code))
    country = country_obj.first()
    
    if not country:
        return # Should not happen if country was seeded correctly

    inserted_count = 0
    
    for record in raw_data:
        # World Bank structure often has a 'value' field and 'date' field
        value = record.get('value')
        date_str = record.get('date')
        
        # World Bank API returns a lot of null/empty data pages, skip them
        if value is None or date_str is None:
            continue

        try:
            # Transform the API date string ('YYYY') into a Python date object
            data_date = date(int(date_str), 1, 1) 
            
            # 1. Create the Pydantic-based object (EconomicIndicatorCreate)
            indicator_create = EconomicIndicatorCreate(
                country_id=country.id,
                indicator_code=indicator_id,
                date=data_date,
                value=float(value)
            )
            
            # 2. Convert to the MAPPED database model (EconomicIndicator)
            #    This is the crucial step to resolve the "is not mapped" error.
            indicator_db = EconomicIndicator(**indicator_create.model_dump())
            
            # 3. Add the MAPPED model instance to the session
            session.add(indicator_db)
            inserted_count += 1
        
        except Exception as e:
            # Handle parsing errors, like date conversion failure
            print(f"Skipping data point for {country_code} ({indicator_id}) on {date_str}: {e}")
            
    print(f"Inserted {inserted_count} records for {country_code} ({indicator_name})")

