# seed_countries.py
import asyncio
from sqlmodel import Session, select

from app.db.database import create_db_and_tables, engine # Import engine
from app.schemas.countries import Country, Region # Import your new Country model

# Define the base countries you need to start with
base_countries = [
    {"code": "DE", "name": "Germany", "region": Region.EUROPE},
    {"code": "FR", "name": "France", "region": Region.EUROPE},
    {"code": "US", "name": "United States", "region": Region.AMERICA},
    # Add more countries as needed for testing
]

async def seed_data():
    # Ensure tables exist first (Optional, but safe)
    await create_db_and_tables() 

    async with Session(engine) as session:
        print("Seeding countries...")
        for country_data in base_countries:
            # Create the ORM object from the dict
            new_country = Country(**country_data)

            # Check if country code already exists to prevent duplicates
            existing = await session.exec(
                select(Country).where(Country.code == new_country.code)
            )
            if existing.first():
                print(f"Country {new_country.code} already exists. Skipping.")
                continue

            session.add(new_country)
            print(f"Added: {new_country.code} - {new_country.name}")

        await session.commit()
        print("Seeding complete! ✅")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(seed_data())