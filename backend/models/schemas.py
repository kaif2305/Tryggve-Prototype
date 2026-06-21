"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RawIncidentInput(BaseModel):
    """Minimal worker-submitted incident description (text-only helper schema)."""

    raw_text: str


class HazardBoundingBox(BaseModel):
    """Normalized hazard location on an uploaded image (0–1000 scale)."""

    label: str
    ymin: int
    xmin: int
    ymax: int
    xmax: int


class IncidentExtraction(BaseModel):
    """Layer-1 structured extraction from raw incident narrative."""

    title: str
    description: str
    hazard_category: str
    hazards_detected: list[HazardBoundingBox] = Field(
        default_factory=list,
        description="Spatial hazard boxes when an image is provided",
    )


class RootCauseAnalysis(BaseModel):
    """Layer-4 root-cause reasoning grounded in retrieved regulations."""

    five_whys: list[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3–5 progressive why-steps toward root cause",
    )
    mto_classification: Literal["Human", "Technology", "Organisation"]
    hierarchy_of_controls_recommendation: str
    cited_regulation_snippets: list[str] = Field(
        ...,
        min_length=1,
        description="Regulation snippet text the model relied on",
    )


class IncidentReport(BaseModel):
    """Full incident report returned by the API and persisted to the database."""

    id: int
    created_at: datetime
    raw_text: str
    title: str
    description: str
    hazard_category: str
    hazards_detected: list[HazardBoundingBox] = Field(default_factory=list)
    five_whys: list[str]
    mto_classification: Literal["Human", "Technology", "Organisation"]
    hierarchy_of_controls_recommendation: str
    cited_regulation_snippets: list[str]


class ReportResponse(BaseModel):
    """API response for POST /report including optional annotated image."""

    report: IncidentReport
    annotated_image_base64: str | None = None
