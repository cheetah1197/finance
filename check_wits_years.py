import asyncio
import httpx
import datetime
import os
import sys

# --- Configuration (Same as in your main service file) ---

# CRITICAL: Must be HTTPS to avoid 302 errors
WITS_BASE_URL = "https://wits.worldbank.org/API/V1/SDMX/GetData"
TARIFF_DATAFLOW = "TRF_TariffFlows"

# Reliable targets for probing the API
RELIABLE_REPORTER = "USA" 
SIMPLE_HS_CODE = "010100"       # A common 6-digit product code (Live horses)
RELIABLE_INDICATOR = "TRF.T.AVGS.SM" # MFN Simple Average Rate

# Get the API Key from the environment variable
WITS_API_KEY = os.getenv("WITS_API_KEY")

# --- Probe Function ---

async def get_latest_available_year(start_year_guess: int) -> int:
    """
    Probes the WITS API to find the most recent year with available data.
    """
    if not WITS_API_KEY:
        print("🛑 [CRITICAL] WITS_API_KEY environment variable is NOT SET.")
        print("             This is the reason for the 403 error. Please set the key.")
        return datetime.date.today().year - 3 # Default to a safe year
        
    print(f"Starting WITS API probe from year {start_year_guess} with key...")

    current_year = start_year_guess
    
    while current_year >= 2010:
        # Construct the base URL
        url = (
            f"{WITS_BASE_URL}/{TARIFF_DATAFLOW}/"
            f"{RELIABLE_INDICATOR}/{RELIABLE_REPORTER}/WLD/"
            f"{SIMPLE_HS_CODE}/{current_year}"
        )
        # Append the necessary API key parameter
        url_with_key = f"{url}?apikey={WITS_API_KEY}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url_with_key)
                response.raise_for_status()
                json_data = response.json()
                
                if json_data.get('DataSet', {}).get('Series'):
                    print(f"✅ [SUCCESS] Latest available year found: {current_year}")
                    return current_year
                else:
                    print(f"   [PROBE] No data found for year {current_year}. Checking prior year...")

            except httpx.HTTPStatusError as e:
                # 403 (Forbidden) is caught here. 
                # Other errors (like 404 or 400) mean no data for the year.
                print(f"   [PROBE] API error for year {current_year} ({e.response.status_code}). Checking prior year...")
                if e.response.status_code == 403:
                    print("   🛑 Re-check your API Key. The 403 error is an authentication failure.")
                    # Stop probing if we hit a 403, as subsequent calls will also fail
                    return datetime.date.today().year - 3 
            except Exception as e:
                print(f"   [PROBE] General error for year {current_year}: {e}. Checking prior year...")

        current_year -= 1
        await asyncio.sleep(0.5)

    print("⚠️ [FAILURE] Could not find any WITS tariff data since 2010. Defaulting to 2022.")
    return 2022

# --- Main Runner ---

async def main():
    """Entry point for the year-checking script."""
    guess_year = datetime.date.today().year + 1
    
    latest_year = await get_latest_available_year(guess_year)
    
    print("\n--- Summary ---")
    print(f"Latest reliable WITS tariff data year: **{latest_year}**")
    print("-----------------")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
