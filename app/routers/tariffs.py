# app/routers/tariffs.py
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.tariffs import Tariff, TariffBase
# You'll add database imports here later

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


@router.post("/", response_model=Tariff)
async def create_tariff(tariff: TariffBase):
    global next_id
    new_tariff_data = tariff.dict()
    new_tariff_data['id'] = next_id
    
    fake_db[next_id] = new_tariff_data
    next_id += 1
    
    return Tariff(id=new_tariff_data['id'], **new_tariff_data)