# app/main.py
from fastapi import FastAPI
from app.routers import tariffs, economics
from app.core.config import settings

# Use a hardcoded title for now
app = FastAPI(title="Tariffs & Economics API")

# Include the routers, with a common prefix for each module
app.include_router(tariffs.router, prefix="/api/v1/tariffs", tags=["Tariffs"])
app.include_router(economics.router, prefix="/api/v1/economics", tags=["Economics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}