from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession # Use AsyncSession for async db ops

# Import models, database tools, and new API schemas
from app.db.database import get_session 
from app.schemas.economics import EconomicIndicator, EconomicIndicatorCreate, EconomicIndicatorRead
from app.schemas.countries import Country # <--- Assuming your Country model is here
from app.schemas.api import CountryEconomicResponse, IndicatorDataPoint # <--- New API Schemas

# Initialize templates here (or import from main if preferred, but initializing here is common)
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["Economics"])

# --- EXISTING ROUTES (UPDATED TO USE ASYNCSESSION) ---

# GET all economic indicators
@router.get("/", response_model=List[EconomicIndicatorRead])
async def read_indicators(session: AsyncSession = Depends(get_session)):
    statement = select(EconomicIndicator)
    results = await session.exec(statement)
    indicators = results.all()
    return indicators

# POST a new economic indicator
@router.post("/", response_model=EconomicIndicatorRead)
async def create_indicator(indicator_in: EconomicIndicatorCreate, session: AsyncSession = Depends(get_session)):
    db_indicator = EconomicIndicator.model_validate(indicator_in)
    
    session.add(db_indicator)
    try:
        await session.commit()
    except Exception as e:
        # Handle unique constraint violation if necessary
        raise HTTPException(status_code=400, detail="Indicator already exists for this country and date.")
        
    await session.refresh(db_indicator)
    return db_indicator

# --------------------------------------------------------------------------
# --- NEW ROUTE FOR COUNTRY-SPECIFIC DATA RETRIEVAL ---
# --------------------------------------------------------------------------

@router.get("/country/{country_code}", response_class=HTMLResponse)
async def get_country_data_html( # Renamed to avoid collision with the JSON route, if you keep both
    request: Request, # <-- REQUIRED: Used by Jinja2 to render the template
    country_code: str, 
    session: AsyncSession = Depends(get_session)
):
    """
    Retrieves and displays economic indicator data for a specific country in HTML.
    """
    code_upper = country_code.upper()
    
    # 1. Fetch Country and Indicator Data (same logic as before)
    country_stmt = select(Country).where(Country.code == code_upper)
    country_result = await session.exec(country_stmt)
    country = country_result.first()

    if not country:
        raise HTTPException(status_code=404, detail=f"Country '{country_code}' not found.")

    indicator_stmt = select(EconomicIndicator).where(EconomicIndicator.country_id == country.id)
    indicator_result = await session.exec(indicator_stmt)
    indicators = indicator_result.all() # <-- This contains the list of all data points
    
    # 2. Render the HTML template
    return templates.TemplateResponse( # <-- USED: The Jinja2 object called to render the template
        "country_data.html", 
        {
            "request": request,             # Pass the Request object
            "country": country,             # Pass the Country SQLModel object
            "data": indicators              # Pass the list of EconomicIndicator objects
        }
    )