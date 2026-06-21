"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent


def _discover_env_files() -> tuple[str, ...] | None:
    """Return existing .env paths for optional local loading (never required in production)."""
    paths = [p for p in (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env") if p.exists()]
    return tuple(str(p) for p in paths) or None


def _is_deployed_environment() -> bool:
    """True on Render and other production hosts where injected env vars are authoritative."""
    return bool(os.getenv("RENDER")) or os.getenv("ENVIRONMENT", "").lower() == "production"


class Settings(BaseSettings):
    """Runtime settings for the safety-reporting prototype.

    SQLite is used for zero-setup local dev; swap ``DATABASE_URL`` for Postgres
    (e.g. ``postgresql+psycopg2://...``) before any real deployment.
    """

    model_config = SettingsConfigDict(
        env_file=_discover_env_files(),
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
        """Prefer injected env on Render; prefer .env locally to avoid stale shell exports."""
        if _is_deployed_environment():
            return (env_settings, dotenv_settings, init_settings, file_secret_settings)
        return (dotenv_settings, env_settings, init_settings, file_secret_settings)

    ENVIRONMENT: str = "development"
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./tryggve.db"
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    CORS_ORIGINS: str = "*"

    GEMINI_FLASH_MODEL: str = "gemini-3.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    GEMINI_EMBEDDING_DIMENSION: int = 768

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def strip_api_key(cls, value: str) -> str:
        """Normalize whitespace from env / .env values."""
        return value.strip()

    @property
    def gemini_api_key(self) -> str:
        """Resolved Gemini key from Pydantic settings or ``os.environ`` fallback."""
        return (self.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or "").strip()

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
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    @property
    def gemini_configured(self) -> bool:
        """True when a non-empty Gemini API key is available from env or settings."""
        return bool(self.gemini_api_key)

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
