# Use asynchronous http client (httpx) to call WITS API endpoints 
import httpx
import asyncio
from typing import List, Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import date

# Import your models and schemas
from app.schemas.tariffs import Tariff, TariffCreate
from app.schemas.countries import Country 
from app.services.helpers import chunk_list # <-- NOW RESOLVED

# Import the new static HS code list
from app.data.hs_codes import ALL_HS_6_DIGIT_CODES # <-- NEW IMPORT

# Base URL and Indicators
WITS_BASE_URL = "http://wits.worldbank.org/API/V1/SDMX/GetData"
TARIFF_DATAFLOW = "TRF_TariffFlows"

MFN_INDICATOR = "TRF.T.AVGS.SM"    # MFN Simple Average
PREF_INDICATOR = "TRF.T.AVGPS.SM" # Preferential Simple Average

# --- Configuration for Batching and Time Frame ---
LATEST_YEAR = 2022 # Hardcoded the latest WITS data year for reliability
START_YEAR = LATEST_YEAR - 2 # Fetching 3 years (2020, 2021, 2022)
COUNTRY_BATCH_SIZE = 20 
HS_CODE_BATCH_SIZE = 50 
# -----------------------------------------------------------------

# Store the country code -> ID mapping globally once after the initial fetch
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

# Upsert logic (Assuming the _upsert_tariffs helper is defined as in the previous response)
async def _upsert_tariffs(session: AsyncSession, tariffs: List[Tariff]):
    # ... (Keep the previous _upsert_tariffs implementation here) ...
    pass


async def fetch_and_save_wits_tariffs(session: AsyncSession):
    """
    Controls the bulk fetching process by looping through years, country batches, and HS code batches.
    """
    print(f"--- Starting WITS Tariff Data Fetch from {START_YEAR} to {LATEST_YEAR} ---")
    
    # 1. Fetch all Country IDs and ISO codes
    country_map: Dict[str, int] = await _get_country_ids(session)
    country_codes = list(country_map.keys())
    
    if not country_codes:
        print("WARNING: No country codes found in DB. Skipping tariff fetch.")
        return
    
    # 2. Chunk countries and HS codes into manageable batches
    country_batches = chunk_list(country_codes, COUNTRY_BATCH_SIZE)
    # Use the comprehensive list
    hs_batches = chunk_list(ALL_HS_6_DIGIT_CODES, HS_CODE_BATCH_SIZE) 
    
    # 3. Start the primary iteration loop (Year)
    # Looping newest to oldest
    for year in range(LATEST_YEAR, START_YEAR - 1, -1):
        print(f"\n--- Processing Year: {year} ---")
        
        # 4. Secondary loop (Country Batches)
        for i, reporter_batch in enumerate(country_batches):
            print(f"  > Processing Country Batch {i+1}/{len(country_batches)} ({len(reporter_batch)} reporters)")
            
            # 5. Tertiary loop (HS Code Batches)
            for j, hs_batch in enumerate(hs_batches):
                print(f"    - Processing HS Code Batch {j+1}/{len(hs_batches)} ({len(hs_batch)} codes)")
                
                # --- CORE FETCH AND MERGE ---
                await _fetch_batch(session, reporter_batch, hs_batch, year)
                
                # IMPORTANT: Pause to respect API rate limits and prevent overload
                await asyncio.sleep(0.5) 
            
    print("\n--- WITS Tariff Data Fetch Complete ---")


async def _fetch_batch(session: AsyncSession, reporter_batch: List[str], hs_batch: List[str], year: int):
    """
    Fetches MFN and Preferential rates for a single batch and merges the results.
    """
    # 1. Fetch MFN Data
    mfn_rates = await _get_tariff_data(reporter_batch, hs_batch, MFN_INDICATOR, year)
    
    # 2. Fetch PREFERENTIAL Data (Pause first)
    await asyncio.sleep(0.5) 
    pref_rates = await _get_tariff_data(reporter_batch, hs_batch, PREF_INDICATOR, year)
    
    # 3. MERGE the data (Pass the global map for look up)
    merged_tariffs = _merge_tariff_data(mfn_rates, pref_rates, year)
    
    # 4. Upsert
    if merged_tariffs:
        await _upsert_tariffs(session, merged_tariffs)


async def _get_tariff_data(reporters: List[str], hs_codes: List[str], indicator: str, year: int) -> Dict[str, float]:
    # ... (Keep the previous _get_tariff_data implementation here) ...
    pass

def _merge_tariff_data(mfn_rates: Dict[str, float], pref_rates: Dict[str, float], year: int) -> List[Tariff]:
    """
    Merges the MFN and PREF rate dictionaries and creates a list of Tariff objects.
    Now correctly uses the global COUNTRY_ID_MAP.
    """
    global COUNTRY_ID_MAP
    merged_list: List[Tariff] = []
    
    for key, mfn_rate in mfn_rates.items():
        try:
            reporter_code, product_code = key.split('_')
            
            country_id = COUNTRY_ID_MAP.get(reporter_code)
            if not country_id:
                # Should not happen if data is clean, but a safety break
                print(f"  [WARN] Country code {reporter_code} not found in DB map. Skipping.")
                continue

            pref_rate = pref_rates.get(key)
            
            merged_list.append(
                Tariff(
                    country_id=country_id,
                    product_code=product_code,
                    year=year,
                    mfn_simple_average_rate=mfn_rate,
                    pref_simple_average_rate=pref_rate
                )
            )
        except Exception as e:
            print(f"  [ERROR] Failed to merge data for key {key}: {e}. Skipping data point.")
            continue

    return merged_list