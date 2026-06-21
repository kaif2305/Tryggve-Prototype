"""Shared Google GenAI client factory."""

from functools import lru_cache

from google import genai

from core.config import get_settings
from core.errors import require_gemini_api_key


@lru_cache
def get_genai_client() -> genai.Client:
    """Create a cached GenAI client using the configured API key."""
    require_gemini_api_key()  # fail fast with a clear 503 if missing
    settings = get_settings()
    return genai.Client(api_key=settings.GEMINI_API_KEY)
