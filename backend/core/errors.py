"""Shared API error helpers."""

from fastapi import HTTPException

from core.config import get_settings

_GEMINI_SETUP_HINT = (
    "GEMINI_API_KEY is not configured. Copy .env.example to .env in the project "
    "root and set your key from https://aistudio.google.com/apikey"
)


def require_gemini_api_key() -> str:
    """Return the configured API key or raise HTTP 503 with setup instructions."""
    settings = get_settings()
    if not settings.gemini_configured:
        raise HTTPException(status_code=503, detail=_GEMINI_SETUP_HINT)
    return settings.GEMINI_API_KEY
