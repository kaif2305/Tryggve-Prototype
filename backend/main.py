"""AI Safety Reporting Prototype — FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.genai import errors as genai_errors
from sqlalchemy import inspect, text

from api.v1.endpoints.incidents import router as incidents_v1_router
from core.config import _ENV_FILE, get_settings
from db.models import IncidentReportDB  # noqa: F401 — registers model with Base
from db.session import Base, engine
from services.regulation_store import initialize_regulation_store

logger = logging.getLogger("uvicorn.error")


def _migrate_schema() -> None:
    """Apply lightweight SQLite schema patches (prototype — use Alembic in production)."""
    inspector = inspect(engine)
    if not inspector.has_table("incident_reports"):
        return
    columns = {column["name"] for column in inspector.get_columns("incident_reports")}
    if "hazards_detected" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE incident_reports "
                    "ADD COLUMN hazards_detected TEXT NOT NULL DEFAULT '[]'"
                )
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables and build the regulation vector store on startup."""
    Base.metadata.create_all(bind=engine)
    _migrate_schema()

    settings = get_settings()
    app.state.gemini_ready = False

    if not settings.gemini_configured:
        logger.warning(
            "GEMINI_API_KEY is empty in %s — skipping regulation store init. "
            "Add your key and restart to enable POST /report.",
            _ENV_FILE,
        )
    else:
        try:
            await initialize_regulation_store()
            app.state.gemini_ready = True
        except genai_errors.ClientError as exc:
            logger.error(
                "Gemini API call failed during startup (%s). "
                "Check GEMINI_API_KEY in %s. /health works; /report is disabled until fixed.",
                exc,
                _ENV_FILE,
            )
        except Exception as exc:
            logger.error(
                "Regulation store init failed (%s). /health works; /report may be unavailable.",
                exc,
            )

    yield


app = FastAPI(
    title="AI Safety Reporting Prototype",
    description=(
        "Prototype backend: workers submit short incident narratives and receive "
        "structured safety reports with root-cause analysis grounded in demo regulations."
    ),
    lifespan=lifespan,
)

settings = get_settings()

# Restrict CORS in production via CORS_ORIGINS (comma-separated). Never use "*" with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(incidents_v1_router, prefix="/api/v1")
# Legacy routes without version prefix (prototype backward compatibility).
app.include_router(incidents_v1_router)
