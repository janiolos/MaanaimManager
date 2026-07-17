"""Configuração da aplicação lendo variáveis de ambiente."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "MaanaimManager"
    ENVIRONMENT: Literal["dev", "prod", "test"] = "dev"
    TIMEZONE: str = "America/Sao_Paulo"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://eventa:eventa@localhost:5432/eventa"

    # JWT / Auth
    JWT_SECRET_KEY: str = "changeme-please-generate-a-32-byte-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INACTIVITY_TIMEOUT_SECONDS: int = 1800

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8090"]

    @model_validator(mode="before")
    @classmethod
    def _fix_cors(cls, data: dict) -> dict:
        raw = data.get("BACKEND_CORS_ORIGINS")
        if isinstance(raw, str):
            try:
                data["BACKEND_CORS_ORIGINS"] = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                data["BACKEND_CORS_ORIGINS"] = [
                    o.strip() for o in raw.split(",") if o.strip()
                ]
        return data

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
