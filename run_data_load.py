# run_data_load.py (Simplified)

import asyncio
# ONLY import the specific functions you need to run
from app.services.data_loader import run_full_data_load, load_all_economic_data 
# Note: You need to have either load_economic_indicators or load_all_economic_data 
# defined in data_loader.py. We'll use load_all_economic_data here for simplicity.

async def main():
    """Main execution function to run the full data loading process."""
    print("--- Starting Full Data Load Execution ---")
    
    # Run the Tariff Loader (if you want to run it too)
    # await run_full_data_load() 
    
    # Run the Economic Indicator Loader
    await load_all_economic_data() 
    
    print("--- Full Data Load Execution Complete ---")

if __name__ == "__main__":
    asyncio.run(main())