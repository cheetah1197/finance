# app/routers/economics.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import UniqueConstraint # Need to import this for the __table_args__

from app.db.database import get_session
from app.schemas.economics import EconomicIndicator, EconomicIndicatorCreate, EconomicIndicatorRead

router = APIRouter(tags=["Economics"])

# GET all economic indicators
@router.get("/", response_model=List[EconomicIndicatorRead])
async def read_indicators(session: Session = Depends(get_session)):
    statement = select(EconomicIndicator)
    results = await session.exec(statement)
    indicators = results.all()
    return indicators

# POST a new economic indicator
@router.post("/", response_model=EconomicIndicatorRead)
async def create_indicator(indicator_in: EconomicIndicatorCreate, session: Session = Depends(get_session)):
    db_indicator = EconomicIndicator.model_validate(indicator_in)
    
    session.add(db_indicator)
    try:
        await session.commit()
    except Exception as e:
        # Handle unique constraint violation if necessary (e.g., indicator/date already exists)
        raise HTTPException(status_code=400, detail="Indicator already exists for this country and date.")
        
    await session.refresh(db_indicator)
    return db_indicator

# Note: You would add GET by ID, PUT, and DELETE routes here later.