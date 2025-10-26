# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tariffs & Economics API"
    # DATABASE_URL: str = "..." # You'll add this later

settings = Settings()