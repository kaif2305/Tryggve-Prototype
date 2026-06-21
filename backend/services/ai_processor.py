"""Gemini-powered incident extraction and root-cause analysis."""

from __future__ import annotations

import json

from fastapi import HTTPException
from google.genai import types
from pydantic import ValidationError

from core.config import get_settings
from core.gemini_client import get_genai_client
from models.schemas import IncidentExtraction, RootCauseAnalysis


def _parse_structured_response(response_text: str, schema_cls: type) -> object:
    """Parse model JSON output and validate against a Pydantic schema."""
    data = json.loads(response_text)
    return schema_cls.model_validate(data)


async def _generate_structured(
    *,
    contents: list,
    schema_cls: type,
    correction_hint: str | None = None,
) -> object:
    """Call Gemini with structured JSON output, retrying once on parse failure."""
    settings = get_settings()
    client = get_genai_client()

    request_contents = list(contents)
    if correction_hint:
        request_contents.append(correction_hint)

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema_cls.model_json_schema(),
        temperature=0.2,
    )

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_FLASH_MODEL,
                contents=request_contents,
                config=config,
            )
            if not response.text:
                raise ValueError("Empty model response")
            return _parse_structured_response(response.text, schema_cls)
        except (json.JSONDecodeError, ValueError, TypeError, ValidationError) as exc:
            last_error = exc
            if attempt == 0:
                request_contents = list(contents) + [
                    (
                        "Your previous response was not valid JSON matching the "
                        f"required schema for {schema_cls.__name__}. Return ONLY "
                        "valid JSON with all required fields."
                    )
                ]
                continue
            break

    raise HTTPException(
        status_code=502,
        detail=f"AI structured-output failed after retry: {last_error}",
    )


async def extract_incident(
    raw_text: str,
    image_bytes: bytes | None,
    image_mime_type: str = "image/jpeg",
) -> IncidentExtraction:
    """Extract structured incident fields from worker narrative (and optional photo)."""
    parts: list = [
        (
            "You are an occupational safety analyst. Extract a concise incident "
            "title, a factual description, and a hazard category from the worker "
            "report below. Use standard OSH categories such as Falls, Electrical, "
            "Chemical, Machinery, Ergonomics, Fire, or Slips/Trips.\n\n"
            f"Worker report:\n{raw_text}"
        )
    ]

    if image_bytes:
        parts.append(
            types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type)
        )
        parts[0] = str(parts[0]) + (
            "\n\nAn accompanying photo is attached — incorporate visible hazards "
            "into the description and category. If an image is provided, identify "
            "the primary safety hazards visible in the photo. Return their bounding "
            "box coordinates in hazards_detected using the normalized [0-1000] scale "
            "for ymin, xmin, ymax, and xmax (origin top-left). Include a short "
            "descriptive label for each hazard. If no hazards are visible, return "
            "an empty hazards_detected list."
        )

    result = await _generate_structured(
        contents=parts,
        schema_cls=IncidentExtraction,
    )
    return result  # type: ignore[return-value]


async def analyze_root_cause(
    extraction: IncidentExtraction,
    retrieved_regulations: list[str],
) -> RootCauseAnalysis:
    """Perform grounded 5-Whys root-cause analysis with MTO classification."""
    regulations_block = "\n\n".join(
        f"- {snippet}" for snippet in retrieved_regulations
    )

    prompt = f"""You are an occupational safety investigator performing root-cause analysis.

INCIDENT SUMMARY
Title: {extraction.title}
Description: {extraction.description}
Hazard category: {extraction.hazard_category}

REFERENCE REGULATION SNIPPETS (demo placeholders — ground your answer ONLY in these):
{regulations_block}

INSTRUCTIONS:
1. Ground your hazard categorization validation and recommendation ONLY in the
   regulation snippets above. In cited_regulation_snippets, copy the exact snippet
   text you relied on (one or more full snippets from the list).
2. Produce a 5-Whys chain of 3–5 steps that progressively drills toward a root cause.
3. Classify the root cause as exactly one of: Human, Technology, Organisation (MTO).
4. Recommend ONE corrective action that respects the Hierarchy of Controls:
   prefer elimination/substitution, then engineering controls, then administrative
   controls; PPE-only fixes are a last resort and should be noted as such.
5. Return JSON matching the required schema."""

    result = await _generate_structured(
        contents=[prompt],
        schema_cls=RootCauseAnalysis,
    )
    return result  # type: ignore[return-value]
