from pydantic_settings import BaseSettings, SettingsConfigDict # Import SettingsConfigDict

class AppSettings(BaseSettings): # Renamed class to AppSettings for clarity
    PROJECT_NAME: str = "Tariffs & Economics API"
    
    # Database Connection String (PostgreSQL format: postgresql+asyncpg://user:password@host/dbname)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:models:25,IT@localhost/finance_db"

    # Use model_config instead of inner Config class for modern Pydantic
    model_config = SettingsConfigDict(
        # Tells Pydantic to load environment variables from a .env file if present
        env_file = ".env", 
        env_file_encoding = 'utf-8'
    )

# CRITICAL STEP: Create the single, instantiated settings object that will be imported.
settings = AppSettings()