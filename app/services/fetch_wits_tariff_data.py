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
from app.services.helpers import chunk_list # We will assume this helper exists or define it below

# Base URL and Indicators
WITS_BASE_URL = "http://wits.worldbank.org/API/V1/SDMX/GetData"
TARIFF_DATAFLOW = "TRF_TariffFlows"

MFN_INDICATOR = "TRF.T.AVGS.SM"    # MFN Simple Average
PREF_INDICATOR = "TRF.T.AVGPS.SM" # Preferential Simple Average

# --- Configuration for Batching and Time Frame ---
# WITS data is often delayed. Check WITS website for the latest available year.
LATEST_YEAR = date.today().year - 3 # Example: If current year is 2025, use 2022. Adjust as needed.
START_YEAR = LATEST_YEAR - 2 # Fetching 3 years of data (e.g., 2020, 2021, 2022)
COUNTRY_BATCH_SIZE = 20 # Max number of countries to include in a single API call
HS_CODE_BATCH_SIZE = 50 # Max number of HS 6-digit codes to include in a single API call

# Placeholder for all HS 6-digit codes (We will populate this later)
# For now, we'll use a small example list that will be chunked.
ALL_HS_6_DIGIT_CODES = ["010190", "847130", "870323", "901890", "040110", "100630", "220410", "392321"] 
# -----------------------------------------------------------------

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
    hs_batches = chunk_list(ALL_HS_6_DIGIT_CODES, HS_CODE_BATCH_SIZE)
    
    # 3. Start the primary iteration loop (Year)
    for year in range(LATEST_YEAR, START_YEAR - 1, -1):
        print(f"\n--- Processing Year: {year} ---")
        
        # 4. Secondary loop (Country Batches)
        for i, reporter_batch in enumerate(country_batches):
            reporter_str = "+".join(reporter_batch)
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
    
    # 3. MERGE the data (See helper below)
    merged_tariffs = _merge_tariff_data(mfn_rates, pref_rates, session, year)
    
    # 4. Upsert
    await _upsert_tariffs(session, merged_tariffs)


async def _get_tariff_data(reporters: List[str], hs_codes: List[str], indicator: str, year: int) -> Dict[str, float]:
    """
    Helper to fetch data for a single indicator (MFN or PREF) and returns a key-value mapping.
    Key format: "COUNTRYCODE_HSCODE" -> Value: tariff_rate
    """
    reporter_list = "+".join(reporters)
    product_list = "+".join(hs_codes)
    
    # WITS URL-based query structure: {DataFlow}/{FREQ.REPORTER.PARTNER.PRODUCT.INDICATOR}.{PERIOD}?format=json
    # PARTNER 'WLD' (World) is used for these simple average indicators
    query_structure = f"A.{reporter_list}.WLD.{product_list}.{indicator}"
    api_url = f"{WITS_BASE_URL}/{TARIFF_DATAFLOW}/{query_structure}.{year}?format=json"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url)
            response.raise_for_status() 
            data = response.json()
            
    except httpx.HTTPStatusError as e:
        print(f"  [ERROR] HTTP error {e.response.status_code} fetching {indicator} data for year {year}. Skipping batch.")
        return {}
    except Exception as e:
        print(f"  [ERROR] Unexpected error during API fetch for {indicator}: {e}. Skipping batch.")
        return {}

    rates_map: Dict[str, float] = {}
    
    try:
        data_series = data['Structure']['KeyFamilies']['KeyFamily']['Components']['Series']
        for series in data_series:
            reporter_code = series['Key']['Reporter']
            product_code = series['Key']['ProductCode']
            
            # Use the key to join later
            key = f"{reporter_code}_{product_code}"
            
            # WITS data always seems to put the observation in the first element of the 'Obs' list
            tariff_rate = float(series['Obs'][0]['Value'])
            rates_map[key] = tariff_rate
            
    except (KeyError, TypeError, IndexError, ValueError) as e:
        # This often means no data was found for this specific batch/indicator
        # print(f"  [INFO] No or partial data found for {indicator} batch in {year}. Error: {e}")
        pass
        
    return rates_map

def _merge_tariff_data(mfn_rates: Dict[str, float], pref_rates: Dict[str, float], session: AsyncSession, year: int) -> List[Tariff]:
    """
    Merges the MFN and PREF rate dictionaries and creates a list of Tariff objects.
    """
    merged_list: List[Tariff] = []
    
    # We use MFN keys as the base, as MFN data is generally more complete than PREF data
    for key, mfn_rate in mfn_rates.items():
        try:
            reporter_code, product_code = key.split('_')
            
            # Fetch country_id from the session (This requires re-fetching the map or passing it)
            # For simplicity here, we assume the map is available via the session or a passed helper.
            # In your actual implementation, you must ensure the map is available.
            country_id = session.country_id_map.get(reporter_code) if hasattr(session, 'country_id_map') else 1 # Placeholder

            # Placeholder for country_id look up for this demonstration
            # In the full script, we will pass the map. For now, use a placeholder ID
            country_id = 1
            
            # Preferential rate is Optional (may not be in the map if the API returned no data)
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
            print(f"  [ERROR] Failed to merge data for key {key}: {e}")
            continue

    return merged_list

# Placeholder for chunk_list function (put this in app/services/helpers.py)
def chunk_list(data: list, size: int) -> List[List[Any]]:
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(data), size):
        yield data[i:i + size]