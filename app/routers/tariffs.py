from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select # We need Session and select

from app.db.database import get_session 
# Import the correct schemas: Tariff (for reference), TariffCreate (input), TariffRead (output)
from app.schemas.tariffs import Tariff, TariffCreate, TariffRead

router = APIRouter()

# Example: A mock in-memory store until you set up the DB
fake_db = {1: {"country_code": "US", "product_code": "A123", "import_duty_rate": 0.05, "id": 1}}
next_id = 2

@router.get("/{tariff_id}", response_model=Tariff)
async def read_tariff(tariff_id: int):
    # In a real app, you'd query the DB here
    if tariff_id not in fake_db:
        raise HTTPException(status_code=404, detail="Tariff not found")
    
    # We must construct the full response model here since our mock data is incomplete
    data = fake_db[tariff_id]
    return Tariff(id=data['id'], country_code=data['country_code'], product_code=data['product_code'], import_duty_rate=data['import_duty_rate'])


# POST a new tariff
# FIX: Use TariffCreate for input and Session for DB operations
@router.post("/", response_model=TariffRead) # Use TariffRead for the response model
async def create_tariff(
    tariff_in: TariffCreate, # Use the input schema
    session: Session = Depends(get_session) # Get the async DB session
):
    # 1. Convert the Pydantic input model (tariff_in) into an ORM model instance
    # We use model_validate for SQLModel v2+ syntax
    db_tariff = Tariff.model_validate(tariff_in) 
    
    # 2. Add the new object to the session (prepares transaction)
    session.add(db_tariff)
    
    # 3. Commit the transaction to the database (this is where the ID is created)
    await session.commit()
    
    # 4. Refresh the object to pull the auto-generated ID and other DB values back into the object
    await session.refresh(db_tariff)
    
    # 5. Return the refreshed object, which conforms to TariffRead
    return db_tariff