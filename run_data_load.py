# run_data_load.py (Simplified)

import asyncio
# ADD: from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.ext.asyncio.session import AsyncSession 
from app.services.data_loader import load_all_economic_data # Assuming this is the function name now
from app.db.database import engine # You need the engine here to start the async context

async def main():
    print("--- Starting Full Data Load Execution ---")
    
    async with engine.begin() as conn: # This starts the async transaction context
        # FIX IS HERE: Use AsyncSession, not Session
        async with AsyncSession(conn) as session: 
            # Pass the session object to the loader function
            await load_all_economic_data(session) 
    
    print("--- Full Data Load Execution Complete ---")

if __name__ == "__main__":
    asyncio.run(main())