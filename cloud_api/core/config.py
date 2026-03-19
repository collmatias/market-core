"""
Centralized configuration loaded from environment variables.
"""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://cloud_admin:cloud_secret_pass@cloud_db/licenses_db"

    # --- Security ---
    api_secret: str = "change-me-in-production"
    jwt_secret: str = "change-me-jwt-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # --- Rate Limiting ---
    rate_limit_default: str = "60/minute"
    rate_limit_license: str = "30/minute"
    rate_limit_admin: str = "30/minute"

    # --- CORS ---
    cors_origins: str = "*"

    # --- App ---
    app_name: str = "VetCoreSoft Cloud API"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
