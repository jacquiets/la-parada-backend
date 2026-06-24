import os
from pydantic_settings import BaseSettings
from typing import List

from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "La Parada API"
    API_V1_STR: str = "/api/v1"
    
    # Orígenes separados por comas o como JSON list
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        return v
    
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
