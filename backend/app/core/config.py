"""MedLens core configuration — single source of truth for all settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./medlens.db"

    # --- Auth ---
    jwt_secret: str = "medlens_production_jwt_secret_key_clinical_intelligence_2026"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # --- AI ---
    ai_provider: Literal["gemini", "openai"] = "gemini"
    ai_api_key: str = ""
    ai_model: str = "gemini-3.6-flash"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    # --- Uploads ---
    max_upload_size_mb: int = 20

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8001

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
