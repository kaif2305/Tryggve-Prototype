"""Versioned incident reporting API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from core.config import get_settings
from core.errors import require_gemini_api_key
from db.models import IncidentReportDB
from db.session import get_db
from models.schemas import HazardBoundingBox, IncidentReport, ReportResponse
from services.ai_processor import analyze_root_cause, extract_incident
from services.image_utils import draw_hazard_boxes
from services.regulation_store import retrieve_relevant_regulations

router = APIRouter(tags=["incidents"])


def _db_to_schema(row: IncidentReportDB) -> IncidentReport:
    """Map a database row to the public API response model."""
    hazards_raw = getattr(row, "hazards_detected", None) or "[]"
    hazards = [HazardBoundingBox.model_validate(h) for h in json.loads(hazards_raw)]
    return IncidentReport(
        id=row.id,
        created_at=row.created_at,
        raw_text=row.raw_text,
        title=row.title,
        description=row.description,
        hazard_category=row.hazard_category,
        hazards_detected=hazards,
        five_whys=json.loads(row.five_whys),
        mto_classification=row.mto_classification,  # type: ignore[arg-type]
        hierarchy_of_controls_recommendation=row.hierarchy_of_controls_recommendation,
        cited_regulation_snippets=json.loads(row.cited_regulation_snippets),
    )


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    """Trivial liveness check for load balancers and local dev."""
    settings = get_settings()
    gemini_ready = getattr(request.app.state, "gemini_ready", False)
    return {
        "status": "ok",
        "gemini_configured": str(settings.gemini_configured).lower(),
        "gemini_ready": str(gemini_ready).lower(),
    }


@router.post("/report", response_model=ReportResponse)
async def create_report(
    request: Request,
    text: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """Accept a worker narrative (and optional photo) and return a structured report."""
    require_gemini_api_key()
    if not getattr(request.app.state, "gemini_ready", False):
        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini is not ready. Set a valid GEMINI_API_KEY in .env and restart the server."
            ),
        )

    image_bytes: bytes | None = None
    image_mime: str = "image/jpeg"
    if image is not None and image.filename:
        image_bytes = await image.read()
        if image.content_type and image.content_type.startswith("image/"):
            image_mime = image.content_type

    extraction = await extract_incident(text, image_bytes, image_mime)
    regulations = await retrieve_relevant_regulations(extraction.description)
    analysis = await analyze_root_cause(extraction, regulations)

    row = IncidentReportDB(
        raw_text=text,
        title=extraction.title,
        description=extraction.description,
        hazard_category=extraction.hazard_category,
        mto_classification=analysis.mto_classification,
        five_whys=json.dumps(analysis.five_whys),
        hierarchy_of_controls_recommendation=analysis.hierarchy_of_controls_recommendation,
        cited_regulation_snippets=json.dumps(analysis.cited_regulation_snippets),
        hazards_detected=json.dumps([h.model_dump() for h in extraction.hazards_detected]),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    report = _db_to_schema(row)
    annotated_image_base64: str | None = None
    if image_bytes and extraction.hazards_detected:
        annotated_image_base64 = draw_hazard_boxes(image_bytes, extraction.hazards_detected)
    elif image_bytes:
        # Return original image when no boxes were detected so the UI still shows the photo.
        annotated_image_base64 = draw_hazard_boxes(image_bytes, [])

    return ReportResponse(report=report, annotated_image_base64=annotated_image_base64)


@router.get("/reports", response_model=list[IncidentReport])
async def list_reports(db: Session = Depends(get_db)) -> list[IncidentReport]:
    """List all stored reports, newest first (backoffice dashboard data)."""
    rows = (
        db.query(IncidentReportDB)
        .order_by(IncidentReportDB.created_at.desc())
        .all()
    )
    return [_db_to_schema(row) for row in rows]


@router.get("/reports/{report_id}", response_model=IncidentReport)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> IncidentReport:
    """Fetch a single report by id."""
    row = db.query(IncidentReportDB).filter(IncidentReportDB.id == report_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _db_to_schema(row)
