import httpx
import asyncio
import re
from typing import List, Dict, Any, Tuple, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, SQLModel
from datetime import date
from sqlalchemy.dialects.postgresql import insert as pg_insert

# --- Import your models and static data ---
# NOTE: Ensure these imports correctly point to your schema files
from app.schemas.tariffs import Tariff, TariffCreate
from app.schemas.countries import Country 
# Assuming you have a Product schema, needed for the foreign key link
from app.schemas.products import Product 
# UPDATED: Import the product data list generated in the previous step
from app.data.product_list import ALL_HS_PRODUCTS 


# --- Configuration and Helpers ---

# Helper function implemented here for completeness (or import from app.services.helpers)
def chunk_list(input_list: List[Any], chunk_size: int) -> List[List[Any]]:
    """Yield successive n-sized chunks from list."""
    # Note: Use list(generator) to return the full list of chunks
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]


WITS_BASE_URL = "http://wits.worldbank.org/API/V1/SDMX/GetData"
TARIFF_DATAFLOW = "TRF_TariffFlows"

# WITS Indicators and mapping to your database fields
INDICATOR_MAP: Dict[str, str] = {
    "TRF.T.AVGS.SM": "mfn_simple_average_rate", # MFN Simple Average (PMF in WITS metadata)
    "TRF.T.AVGPS.SM": "pref_simple_average_rate", # Preferential Simple Average (PRFP)
    # Added the third indicator for the 'applied_simple_average_rate' field
    "TRF.T.AVGA.SM": "applied_simple_average_rate", # Applied Simple Average (ATF)
}

# --- Configuration for Batching and Time Frame ---
LATEST_YEAR = 2022 
START_YEAR = LATEST_YEAR - 2 
COUNTRY_BATCH_SIZE = 1 # Keep low since we typically focus on one country (USA)
HS_CODE_BATCH_SIZE = 100 # Good size for bulk fetching
# -----------------------------------------------------------------

# Global map for fast lookup
COUNTRY_ID_MAP: Dict[str, int] = {} 

async def _get_country_ids(session: AsyncSession) -> Dict[str, int]:
    """Helper to fetch country codes and IDs from the database."""
    global COUNTRY_ID_MAP
    if COUNTRY_ID_MAP:
        return COUNTRY_ID_MAP
        
    stmt = select(Country.code, Country.id)
    result = await session.exec(stmt)
    COUNTRY_ID_MAP = {code: id for code, id in result.all()}
    return COUNTRY_ID_MAP


async def _upsert_tariffs(session: AsyncSession, tariffs: List[TariffCreate]):
    """
    Performs an efficient batch UPSERT (INSERT OR UPDATE) operation in PostgreSQL.
    """
    if not tariffs:
        return

    # Convert the list of Pydantic models to dictionaries for bulk insertion
    values = [t.model_dump(exclude_none=True) for t in tariffs] # exclude_none is safer
    insert_stmt = pg_insert(Tariff).values(values)
    
    # Define which columns to update on conflict (all the rate columns)
    update_cols = {
        "mfn_simple_average_rate": insert_stmt.excluded["mfn_simple_average_rate"],
        "pref_simple_average_rate": insert_stmt.excluded["pref_simple_average_rate"],
        "applied_simple_average_rate": insert_stmt.excluded["applied_simple_average_rate"],
    }
    
    # Execute the statement, using the unique constraint name from tariffs.py
    upsert_stmt = insert_stmt.on_conflict_do_update(
        constraint='uc_country_product_year', 
        set_=update_cols
    )
    
    try:
        await session.execute(upsert_stmt)
        await session.commit()
        print(f"    [DB] Successfully UPSERTED {len(tariffs)} tariff records.")
    except Exception as e:
        await session.rollback()
        print(f"    [DB ERROR] Failed to perform UPSERT: {e}")


async def _get_tariff_data(reporters: List[str], hs_codes: List[str], indicator: str, year: int) -> Dict[str, Optional[float]]:
    """
    Fetches tariff data for a single batch and a single indicator.
    Returns a dictionary mapping 'REPORTER_CODE_HS_CODE' to the tariff rate.
    """
    
    reporter_str = ".".join(reporters)
    hs_str = ".".join(hs_codes)
    year_str = str(year)

    # WITS URL Format: {base}/{dataflow}/[INDICATOR]/[REPORTERS]/[PARTNERS]/[PRODUCT_CODES]/[TIME]
    url = f"{WITS_BASE_URL}/{TARIFF_DATAFLOW}/{indicator}/{reporter_str}/WLD/{hs_str}/{year_str}"
    
    rates: Dict[str, Optional[float]] = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Simplified retry logic for this example
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            json_data = response.json()
            
            if not json_data.get('DataSet'):
                return rates
            
            # Parse the complex WITS JSON structure
            for series in json_data.get('DataSet', {}).get('Series', []):
                keys = series.get('SeriesKey', {}).get('Value', [])
                reporter_code = keys[0].get('id')
                product_code = keys[4].get('id')
                
                if not reporter_code or not product_code:
                    continue
                    
                observation = series.get('Obs', [{}])[0]
                rate_value = observation.get('ObsValue', {}).get('Value')

                if rate_value is not None:
                    key = f"{reporter_code}_{product_code}"
                    rates[key] = float(rate_value)
                    
            print(f"    [API] Fetched {len(rates)} records for {indicator}.")
            return rates

        except httpx.HTTPStatusError as e:
            print(f"    [API ERROR] HTTP error for {indicator}: {e}")
        except Exception as e:
            print(f"    [API ERROR] Unknown error for {indicator}: {e}")

        return rates


def _merge_tariff_data(all_indicator_rates: Dict[str, Dict[str, Optional[float]]], year: int) -> List[TariffCreate]:
    """
    Merges all indicator rate dictionaries (PMF, PRFP, ATF) into a list of TariffCreate objects.
    """
    global COUNTRY_ID_MAP
    merged_map: Dict[str, TariffCreate] = {}
    
    # Iterate through all indicators and build/update the merged map
    for indicator_code, rates in all_indicator_rates.items():
        db_field = INDICATOR_MAP.get(indicator_code)
        if not db_field: continue
        
        for key, rate in rates.items():
            reporter_code, product_code = key.split('_')
            country_id = COUNTRY_ID_MAP.get(reporter_code)
            
            if not country_id: continue
            
            if key not in merged_map:
                # Create the base object if it doesn't exist
                merged_map[key] = TariffCreate(
                    country_id=country_id,
                    product_code=product_code,
                    year=year,
                    mfn_simple_average_rate=None,
                    pref_simple_average_rate=None,
                    applied_simple_average_rate=None
                )
            
            # Use setattr to dynamically update the correct field (e.g., 'mfn_simple_average_rate')
            setattr(merged_map[key], db_field, rate)
                
    return list(merged_map.values())


async def _fetch_batch(session: AsyncSession, reporter_batch: List[str], hs_batch: List[str], year: int):
    """
    Fetches MFN, PREF, and ATF rates for a single batch and merges the results.
    """
    tasks: List[asyncio.Future] = []
    
    # Create a task for each required indicator
    for indicator_code in INDICATOR_MAP.keys():
        tasks.append(_get_tariff_data(reporter_batch, hs_batch, indicator_code, year))

    # Run all three indicator fetches concurrently
    all_results = await asyncio.gather(*tasks)

    # all_results is a list of Dictionaries of the form: [mfn_rates, pref_rates, applied_rates]
    all_indicator_rates: Dict[str, Dict[str, Optional[float]]] = {
        indicator: result 
        for indicator, result in zip(INDICATOR_MAP.keys(), all_results)
    }
    
    # 3. MERGE the data
    merged_tariffs = _merge_tariff_data(all_indicator_rates, year)
    
    # 4. Upsert
    if merged_tariffs:
        await _upsert_tariffs(session, merged_tariffs)


async def fetch_and_save_wits_tariffs(session: AsyncSession):
    """
    Controls the bulk fetching process. This is the main function to be called from your API.
    """
    print(f"--- Starting WITS Tariff Data Fetch from {START_YEAR} to {LATEST_YEAR} ---")
    
    # 1. Fetch all Country IDs and ISO codes
    country_map: Dict[str, int] = await _get_country_ids(session)
    country_codes = list(country_map.keys())
    
    if not country_codes:
        print("WARNING: No country codes found in DB. Please pre-load your target country (e.g., 'USA'). Skipping tariff fetch.")
        return
    
    # 2. Extract HS codes from the product list (using the corrected product_list structure)
    all_hs_codes = [p['code'] for p in ALL_HS_PRODUCTS]
    
    if not all_hs_codes:
        print("WARNING: No product codes found in ALL_HS_PRODUCTS. Skipping tariff fetch.")
        return

    country_batches = chunk_list(country_codes, COUNTRY_BATCH_SIZE)
    hs_batches = chunk_list(all_hs_codes, HS_CODE_BATCH_SIZE) 
    
    # 3. Start the primary iteration loop (Year)
    for year in range(LATEST_YEAR, START_YEAR - 1, -1):
        print(f"\n--- Processing Year: {year} ---")
        
        # 4. Secondary loop (Country Batches)
        for i, reporter_batch in enumerate(country_batches):
            print(f" > Processing Country Batch {i+1}/{len(country_batches)} ({len(reporter_batch)} reporters)")
            
            # 5. Tertiary loop (HS Code Batches)
            for j, hs_batch in enumerate(hs_batches):
                print(f"   - Processing HS Code Batch {j+1}/{len(hs_batches)} ({len(hs_batch)} codes)")
                
                # --- CORE FETCH AND MERGE ---
                await _fetch_batch(session, reporter_batch, hs_batch, year)
                
                # IMPORTANT: Pause to respect API rate limits
                await asyncio.sleep(1.0)
            
    print("\n--- WITS Tariff Data Fetch Complete ---")
