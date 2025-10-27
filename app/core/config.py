
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tariffs & Economics API"
    
    # Database Connection String (PostgreSQL format: postgresql+asyncpg://user:password@host/dbname)
    # Set this as an environment variable when running the app later!
    DATABASE_URL: str = "postgresql+asyncpg://postgres:models:25,IT@localhost/finance_db"

    class Config:
        # Tells Pydantic to load environment variables from a .env file if present
        env_file = ".env"

settings = Settings()
