import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "La Parada API"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"] # Configure appropriately for production
    
    # Database
    # Railway provides DATABASE_URL environment variable natively for PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    # Supabase (útil si utilizas el cliente supabase-py para autenticación o storage)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    # Service Role Key — solo backend, nunca exponer en el frontend
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
