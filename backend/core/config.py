"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from monorepo root (or backend/) so local dev works from any CWD.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_ENV_FILE = _REPO_ROOT / ".env"
if not _ENV_FILE.exists():
    _ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime settings for the safety-reporting prototype.

    SQLite is used for zero-setup local dev; swap ``DATABASE_URL`` for Postgres
    (e.g. ``postgresql+psycopg2://...``) before any real deployment.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """In production, container env vars win over baked-in dotenv files."""
        if os.getenv("ENVIRONMENT", "").lower() == "production":
            return (env_settings, dotenv_settings, init_settings)
        return (dotenv_settings, env_settings, init_settings)

    ENVIRONMENT: str = "development"
    # Empty default allows the server to boot for /health; AI routes validate at call time.
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./tryggve.db"
    # When set, these build a URL-safe Postgres connection string (handles @, #, etc. in passwords).
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    # Comma-separated origins, e.g. "https://app.example.com". Use "*" only in local dev.
    CORS_ORIGINS: str = "*"

    # Model IDs checked against google-genai SDK docs at build time (Jun 2026).
    # See https://ai.google.dev/gemini-api/docs/models — update when deprecated.
    GEMINI_FLASH_MODEL: str = "gemini-3.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    GEMINI_EMBEDDING_DIMENSION: int = 768

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def strip_api_key(cls, value: str) -> str:
        """Normalize whitespace from .env values."""
        return value.strip()

    @property
    def database_url(self) -> str:
        """Return the SQLAlchemy database URL, building Postgres DSN when components are set."""
        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            user = quote_plus(self.POSTGRES_USER)
            password = quote_plus(self.POSTGRES_PASSWORD)
            host = self.POSTGRES_HOST or "db"
            return (
                f"postgresql+psycopg2://{user}:{password}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        url = self.DATABASE_URL
        # Render/Heroku provide postgresql:// — SQLAlchemy needs the psycopg2 driver.
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    @property
    def gemini_configured(self) -> bool:
        """Return True when a non-empty Gemini API key is present."""
        return bool(self.GEMINI_API_KEY)

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS_ORIGINS into a list for FastAPI middleware."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
