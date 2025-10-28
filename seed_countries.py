# seed_countries.py
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession # Import the asynchronous version
from sqlmodel import select # Keep select
from sqlalchemy import text # Import text for executing simple checks if needed

from app.db.database import create_db_and_tables, engine 
from app.schemas.countries import Country, Region 

# --- COMPLETE COUNTRY LIST (Use this for Seeding) ---
# Note: This is a representative list of UN members + common territories.
COUNTRIES_DATA = [
    # EUROPE
    {"code": "DE", "name": "Germany", "region": Region.EUROPE},
    {"code": "FR", "name": "France", "region": Region.EUROPE},
    {"code": "GB", "name": "United Kingdom", "region": Region.EUROPE},
    {"code": "IT", "name": "Italy", "region": Region.EUROPE},
    {"code": "ES", "name": "Spain", "region": Region.EUROPE},
    {"code": "NL", "name": "Netherlands", "region": Region.EUROPE},
    {"code": "BE", "name": "Belgium", "region": Region.EUROPE},
    {"code": "SE", "name": "Sweden", "region": Region.EUROPE},
    {"code": "CH", "name": "Switzerland", "region": Region.EUROPE},
    {"code": "PL", "name": "Poland", "region": Region.EUROPE},
    {"code": "IE", "name": "Ireland", "region": Region.EUROPE},
    {"code": "GR", "name": "Greece", "region": Region.EUROPE},
    {"code": "PT", "name": "Portugal", "region": Region.EUROPE},
    {"code": "AT", "name": "Austria", "region": Region.EUROPE},
    {"code": "NO", "name": "Norway", "region": Region.EUROPE},
    {"code": "DK", "name": "Denmark", "region": Region.EUROPE},
    {"code": "FI", "name": "Finland", "region": Region.EUROPE},
    {"code": "CZ", "name": "Czechia", "region": Region.EUROPE},
    {"code": "HU", "name": "Hungary", "region": Region.EUROPE},
    {"code": "RO", "name": "Romania", "region": Region.EUROPE},
    {"code": "BG", "name": "Bulgaria", "region": Region.EUROPE},
    {"code": "HR", "name": "Croatia", "region": Region.EUROPE},
    {"code": "SK", "name": "Slovakia", "region": Region.EUROPE},
    {"code": "LT", "name": "Lithuania", "region": Region.EUROPE},
    {"code": "LV", "name": "Latvia", "region": Region.EUROPE},
    {"code": "EE", "name": "Estonia", "region": Region.EUROPE},
    {"code": "CY", "name": "Cyprus", "region": Region.EUROPE},
    {"code": "MT", "name": "Malta", "region": Region.EUROPE},
    {"code": "LU", "name": "Luxembourg", "region": Region.EUROPE},
    {"code": "IS", "name": "Iceland", "region": Region.EUROPE},
    
    # AMERICA (North, Central, and South)
    {"code": "US", "name": "United States", "region": Region.AMERICA},
    {"code": "CA", "name": "Canada", "region": Region.AMERICA},
    {"code": "MX", "name": "Mexico", "region": Region.AMERICA},
    {"code": "BR", "name": "Brazil", "region": Region.AMERICA},
    {"code": "AR", "name": "Argentina", "region": Region.AMERICA},
    {"code": "CL", "name": "Chile", "region": Region.AMERICA},
    {"code": "CO", "name": "Colombia", "region": Region.AMERICA},
    {"code": "PE", "name": "Peru", "region": Region.AMERICA},
    {"code": "VE", "name": "Venezuela", "region": Region.AMERICA},
    {"code": "EC", "name": "Ecuador", "region": Region.AMERICA},
    {"code": "CU", "name": "Cuba", "region": Region.AMERICA},
    {"code": "JM", "name": "Jamaica", "region": Region.AMERICA},
    {"code": "PR", "name": "Puerto Rico", "region": Region.AMERICA}, # Territory
    
    # ASIA
    {"code": "CN", "name": "China", "region": Region.ASIA},
    {"code": "JP", "name": "Japan", "region": Region.ASIA},
    {"code": "IN", "name": "India", "region": Region.ASIA},
    {"code": "KR", "name": "South Korea", "region": Region.ASIA},
    {"code": "ID", "name": "Indonesia", "region": Region.ASIA},
    {"code": "SA", "name": "Saudi Arabia", "region": Region.ASIA},
    {"code": "TR", "name": "Turkey", "region": Region.ASIA},
    {"code": "TH", "name": "Thailand", "region": Region.ASIA},
    {"code": "MY", "name": "Malaysia", "region": Region.ASIA},
    {"code": "VN", "name": "Vietnam", "region": Region.ASIA},
    {"code": "PH", "name": "Philippines", "region": Region.ASIA},
    {"code": "PK", "name": "Pakistan", "region": Region.ASIA},
    {"code": "SG", "name": "Singapore", "region": Region.ASIA},
    {"code": "AE", "name": "United Arab Emirates", "region": Region.ASIA},
    {"code": "IL", "name": "Israel", "region": Region.ASIA},
    
    # AFRICA (A representative sample)
    {"code": "ZA", "name": "South Africa", "region": Region.AFRICA},
    {"code": "EG", "name": "Egypt", "region": Region.AFRICA},
    {"code": "NG", "name": "Nigeria", "region": Region.AFRICA},
    {"code": "KE", "name": "Kenya", "region": Region.AFRICA},
    {"code": "MA", "name": "Morocco", "region": Region.AFRICA},
    
    # OCEANIA (A representative sample)
    {"code": "AU", "name": "Australia", "region": Region.OCEANIA},
    {"code": "NZ", "name": "New Zealand", "region": Region.OCEANIA},
]

async def seed_data():
    # Only ensure tables exist if you want this script to also act as a full init script
    # await create_db_and_tables() 
    
   async with AsyncSession(engine) as session:
        print("Seeding countries...")
        count = 0
        for country_data in COUNTRIES_DATA:
            new_country = Country(**country_data)
            
            # Check if country code already exists to prevent duplicates
            existing = await session.exec(
                select(Country).where(Country.code == new_country.code)
            )
            if existing.first():
                # print(f"Country {new_country.code} already exists. Skipping.")
                continue
            
            session.add(new_country)
            count += 1

        await session.commit()
        print(f"Seeding complete! Added {count} new countries. ✅")

if __name__ == "__main__":
    asyncio.run(seed_data())