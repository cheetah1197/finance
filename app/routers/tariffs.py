# app/routers/tariffs.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db.database import get_session
from app.schemas.tariffs import Tariff, TariffCreate, TariffRead # All schemas needed
from app.schemas.countries import Country # Needed to help with lookups/joins if necessary

router = APIRouter(tags=["Tariffs"])

# 1. CREATE (POST /tariffs/)
@router.post("/", response_model=TariffRead, status_code=status.HTTP_201_CREATED)
async def create_tariff(
    tariff_in: TariffCreate,
    session: Session = Depends(get_session)
):
    """Creates a new tariff record."""
    # Ensure country_id exists before insertion (Foreign Key integrity)
    country_exists = await session.get(Country, tariff_in.country_id)
    if not country_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Country ID {tariff_in.country_id} does not exist."
        )

    db_tariff = Tariff.model_validate(tariff_in)
    session.add(db_tariff)
    
    try:
        await session.commit()
    except Exception as e:
        # Handle unique constraint violation (country_id, product_code combination)
        if "uc_country_product" in str(e):
            raise HTTPException(status_code=400, detail="Tariff already exists for this country and product code.")
        raise  # Re-raise other exceptions
        
    await session.refresh(db_tariff)
    return db_tariff


# 2. READ ALL (GET /tariffs/)
@router.get("/", response_model=List[TariffRead])
async def read_tariffs(
    offset: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Retrieves a list of all tariff records with optional pagination."""
    statement = select(Tariff).offset(offset).limit(limit)
    results = await session.exec(statement)
    tariffs = results.all()
    return tariffs


# 3. READ SINGLE (GET /tariffs/{tariff_id})
@router.get("/{tariff_id}", response_model=TariffRead)
async def read_tariff_by_id(
    tariff_id: int, 
    session: Session = Depends(get_session)
):
    """Retrieves a single tariff record by its ID."""
    tariff = await session.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return tariff


# 4. UPDATE (PUT /tariffs/{tariff_id})
@router.put("/{tariff_id}", response_model=TariffRead)
async def update_tariff(
    tariff_id: int, 
    tariff_update: TariffCreate, # Use the Create schema for update input
    session: Session = Depends(get_session)
):
    """Updates an existing tariff record."""
    db_tariff = await session.get(Tariff, tariff_id)
    if not db_tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    
    # Apply updates from the input schema to the database object
    update_data = tariff_update.model_dump(exclude_unset=True)
    db_tariff.sqlmodel_update(update_data) # sqlmodel_update seems not to be called
    
    session.add(db_tariff)
    await session.commit()
    await session.refresh(db_tariff)
    return db_tariff


# 5. DELETE (DELETE /tariffs/{tariff_id})
@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tariff(
    tariff_id: int, 
    session: Session = Depends(get_session)
):
    """Deletes a tariff record by its ID."""
    tariff = await session.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    
    await session.delete(tariff)
    await session.commit()
    return {"ok": True}