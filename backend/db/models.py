"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class IncidentReportDB(Base):
    """Persisted safety incident report."""

    __tablename__ = "incident_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hazard_category: Mapped[str] = mapped_column(String(200), nullable=False)
    mto_classification: Mapped[str] = mapped_column(String(50), nullable=False)
    five_whys: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded list
    hierarchy_of_controls_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    cited_regulation_snippets: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded list
    hazards_detected: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON-encoded list
