from typing import Optional, List

# FIX: Import AsyncSession from the correct location
from sqlmodel.ext.asyncio.session import AsyncSession 
from sqlmodel import select
from sqlalchemy.dialects.postgresql import insert

# Ensure these imports point to your schema files
from app.schemas.tariffs import TariffCreate, Tariff, TariffRead
# Assuming Country and Product models are also needed for relationship queries
from app.schemas.countries import Country
from app.schemas.products import Product

# --- BULK INGESTION ---

async def create_tariffs_bulk(
    session: AsyncSession, 
    tariffs: List[TariffCreate]
) -> List[Tariff]:
    """
    Performs a high-performance bulk UPSERT (INSERT or UPDATE) 
    using the dedicated PostgreSQL ON CONFLICT clause.
    """
    if not tariffs:
        return []

    # 1. Convert models to dictionaries for bulk insertion
    values_to_insert = [t.model_dump() for t in tariffs]

    # 2. Define the core INSERT statement
    insert_stmt = insert(Tariff).values(values_to_insert)

    # 3. Define the UPSERT logic (Update if Conflict)
    on_conflict_stmt = insert_stmt.on_conflict_do_update(
        # The unique constraint defined in Tariff model
        index_elements=['country_id', 'product_code', 'year'],
        set_={
            Tariff.mfn_simple_average_rate: insert_stmt.excluded.mfn_simple_average_rate,
            Tariff.pref_simple_average_rate: insert_stmt.excluded.pref_simple_average_rate,
            Tariff.applied_simple_average_rate: insert_stmt.excluded.applied_simple_average_rate,
        }
    )

    # 4. Execute and Commit
    await session.exec(on_conflict_stmt)
    await session.commit()
    
    # We return the original list as a sign of successful operation
    return tariffs

# --- DATA RETRIEVAL ---

async def get_tariffs_by_country(
    session: AsyncSession, 
    country_id: int, 
    year: Optional[int] = None
) -> List[TariffRead]:
    """
    Retrieves all tariff data for a given country, optionally filtered by year.
    Uses indexed columns for fast retrieval.
    """
    
    # Base query: select Tariff where country_id matches
    query = select(Tariff).where(Tariff.country_id == country_id)

    # Apply optional year filter
    if year is not None:
        query = query.where(Tariff.year == year)

    # Execute the query and fetch all results
    result = await session.exec(query)
    tariffs = result.scalars().all()
    
    # Use model_validate for conversion to the TariffRead schema
    return [TariffRead.model_validate(t) for t in tariffs]


async def get_single_tariff_rate(
    session: AsyncSession,
    country_id: int,
    product_code: str,
    year: int
) -> Optional[TariffRead]:
    """
    Retrieves a single, specific tariff record using all three unique keys.
    This is the fastest possible retrieval query.
    """
    query = select(Tariff).where(
        (Tariff.country_id == country_id) & 
        (Tariff.product_code == product_code) & 
        (Tariff.year == year)
    )
    
    # scalar_one_or_none is best for fetching a single result
    result = await session.execute(query)
    tariff = result.scalar_one_or_none()
    
    if tariff:
        return TariffRead.model_validate(tariff)
    return None
