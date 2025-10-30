import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession 
from app.db.database import engine # Assuming you have the engine imported here
from app.services.data_loader import (
    load_all_economic_data,
    retrieve_all_economic_data # <--- New import for data access
) 

async def main():
    print("--- Starting Full Data Load and Retrieval Execution ---")
    
    # 1. Start the async connection/transaction context
    async with engine.begin() as conn: 
        
        # 2. Open the AsyncSession using the connection
        async with AsyncSession(conn) as session: 
            
            # A. Load Data: Fetch from World Bank API and insert into the database
            print("Starting World Bank API fetch and database insertion...")
            await load_all_economic_data(session) 
            
            # B. Retrieve Data: Query and display the newly inserted data
            print("\nStarting database retrieval and printing sample data...")
            await retrieve_all_economic_data(session)
    
    print("--- Full Data Load and Retrieval Execution Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
