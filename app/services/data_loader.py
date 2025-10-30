import httpx
import asyncio
from datetime import date
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
# Import for the UPSERT logic
from sqlalchemy.dialects.postgresql import insert 

from app.db.database import engine # Assuming engine is defined here or imported

# --- Imports for Models (Adjust paths as needed) ---
from app.schemas.countries import Country  # Assuming Country is in app.models.country
from app.schemas.economics import EconomicIndicatorCreate, EconomicIndicator 

# --- New Constants for World Bank Indicators ---

# The full list of indicator IDs to fetch
TARGET_INDICATORS = {
    "REAL_GDP_GROWTH": "NY.GDP.MKTP.KD.ZG",
    "NOMINAL_GDP": "NY.GDP.MKTP.CD",
    "REAL_GDP_PCAP": "NY.GDP.PCAP.KD",
    "NOMINAL_GDP_PCAP": "NY.GDP.PCAP.CD",
    "PRIVATE_INVEST": "NE.GDI.FPRV.CD",
    "EMPLOYMENT_RATIO": "SL.EMP.TOTL.SP.ZS",
    "CPI_INFLATION": "FP.CPI.TOTL.ZG",
}

# Base API URL template for fetching an indicator (uses f-string formatting placeholders)
WORLD_BANK_API_URL = (
    "https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_id}"
    "?date={date_range}&format=json&per_page=500"
)


# --- WORLD BANK API Functions ---

async def fetch_worldbank_data(client: httpx.AsyncClient, country_code: str, indicator_id: str, date_range: str) -> list:
    """Fetches ALL pages of data for a specific country and indicator."""
    all_records = []
    page = 1
    total_pages = 1 

    while page <= total_pages:
        # Construct the URL for the specific country, indicator, and page number
        url = (
            f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_id}"
            f"?date={date_range}&format=json&per_page=500&page={page}"
        )
        
        try:
            response = await client.get(url)
            response.raise_for_status()
            response_data = response.json()

            if not response_data or len(response_data) < 2:
                break 

            metadata = response_data[0]
            data_page = response_data[1]
            
            total_pages = metadata.get('pages', 1)
            
            if data_page:
                all_records.extend(data_page)
            
            page += 1
            await asyncio.sleep(0.1) 

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error fetching {country_code} for {indicator_id}: {e.response.status_code}")
            break
        except Exception as e:
            print(f"General error fetching data for {country_code} ({indicator_id}): {e}")
            break
            
    return all_records

async def _process_and_insert_indicator(client: httpx.AsyncClient, session: AsyncSession, country_code: str, indicator_id: str, indicator_name: str, date_range: str):
    """Helper to fetch, transform, and UPSERT data for one indicator/country pair."""
    
    raw_data = await fetch_worldbank_data(client, country_code, indicator_id, date_range)
    
    # Safely retrieve the Country object using the passed session
    country_obj = await session.exec(select(Country).where(Country.code == country_code))
    country = country_obj.first()
    
    if not country:
        print(f"Error: Country code {country_code} not found in DB.")
        return 

    data_to_upsert = []
    inserted_count = 0
    
    for record in raw_data:
        value = record.get('value')
        date_str = record.get('date')
        
        if value is None or date_str is None:
            continue

        try:
            data_date = date(int(date_str), 1, 1) 
            
            # Prepare data dictionary for UPSERT (batch operation)
            data_to_upsert.append({
                "country_id": country.id,
                "indicator_code": indicator_id,
                "date": data_date,
                "value": float(value),
            })
            inserted_count += 1
        
        except Exception as e:
            print(f"Skipping data point for {country_code} ({indicator_id}) on {date_str}: {e}")
            
    if data_to_upsert:
        # Define the INSERT statement for PostgreSQL
        stmt = insert(EconomicIndicator).values(data_to_upsert)
        
        # Configure the UPSERT logic to handle duplicate key violations
        stmt = stmt.on_conflict_do_update(
            # The name of the unique constraint causing the error
            constraint="uc_econ_data", 
            # If conflict occurs, update only the 'value' column
            set_={"value": stmt.excluded.value}
        )

        # Execute the UPSERT statement directly on the connection
        try:
            await session.execute(stmt)
        except Exception as e:
            print(f"Error during UPSERT for {country_code} ({indicator_id}): {e}")

    # print(f"Processed {inserted_count} records for {country_code} ({indicator_name})")


async def load_all_economic_data(session: AsyncSession):
    """Top-level function to orchestrate the World Bank data load."""
    print("--- Starting World Bank Economic Data Load ---")

    country_codes_result = await session.exec(select(Country.code))
    country_codes = country_codes_result.all()

    DATE_RANGE = "2020:2024" 
    tasks = []

    async with httpx.AsyncClient(timeout=30.0) as client: 
        for country_code in country_codes:
            for indicator_name, indicator_id in TARGET_INDICATORS.items():
                task = _process_and_insert_indicator(
                    client=client, 
                    session=session,
                    country_code=country_code, 
                    indicator_id=indicator_id, 
                    indicator_name=indicator_name, 
                    date_range=DATE_RANGE
                )
                tasks.append(task)

        # Wait for all concurrent API calls and data preparation to finish
        await asyncio.gather(*tasks)

        # COMMIT ALL CHANGES AT ONCE
        await session.commit()
            
    print("--- World Bank economic data load FINISHED ---")


async def retrieve_all_economic_data(session: AsyncSession):
    """
    Retrieves and prints a sample of economic indicator data from the database
    after the load operation has completed.
    """
    print("\n--- Starting Data Retrieval Sample ---")
    
    # Query to select a sample of records from the EconomicIndicator table
    statement = select(EconomicIndicator).limit(10)
    
    result = await session.exec(statement)
    all_data = result.scalars().all()

    print(f"Total records retrieved (showing max 10): {len(all_data)}")
    
    # Print sample data
    if all_data:
        print("\n[Sample Data Structure]")
        print("----------------------------------------------------------------------")
        print("{:<12} {:<20} {:<10} {:<15}".format("Country ID", "Indicator Code", "Date", "Value"))
        print("----------------------------------------------------------------------")
        for record in all_data:
            print("{:<12} {:<20} {:<10} {:<15.2f}".format(
                record.country_id,
                record.indicator_code,
                record.date.year,
                record.value
            ))
        print("----------------------------------------------------------------------")
    else:
        print("No economic indicator data found in the database.")
        
    print("--- Data Retrieval Sample Finished ---")
    return all_data