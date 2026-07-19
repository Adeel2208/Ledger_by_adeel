"""Inbound application endpoints (FR-4, Epic C).

Minimum input is deck + company name — do not add required fields (non-negotiable).
Flow: upload deck -> parse to signals (slide-tagged provenance) -> dedup/ingest ->
fast first-pass screening. The founder gets a decision + stated reason immediately.
"""
from __future__ import annotations

import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence.screening import first_pass
from app.memory.ingestion.base import IngestBundle
from app.memory.ingestion.deck_parser import DeckConnector
from app.memory.repository import MemoryRepository
from app.services import profile_service
from app.services.ingestion_service import IngestionService
from app.services.profile_service import ProfileError

logger = logging.getLogger(__name__)
router = APIRouter()

_UPLOAD_DIR = os.path.join("data", "uploads")
_ALLOWED_EXT = {".pdf", ".pptx", ".docx"}


@router.post("")
async def create_application(
    company_name: str = Form(...),
    deck: UploadFile | None = File(None),
    founder_name: str | None = Form(None),   # optional — helps dedup, never required
    founder_email: str | None = Form(None),  # optional
    # Founder-supplied profile. All optional: a missing field is a disclosed
    # gap on the profile, never a blocker on the application.
    founder_photo: UploadFile | None = File(None),
    founder_headline: str | None = Form(None),
    founder_bio: str | None = Form(None),
    founder_role: str | None = Form(None),
    founder_location: str | None = Form(None),
    founder_linkedin: str | None = Form(None),
    db: Session = Depends(get_db),
) -> dict:
    """Accept deck + company name, ingest, and run the fast first-pass filter."""
    warnings: list[str] = []
    bundle = IngestBundle(
        signals=[],
        identity={"name": founder_name, "email": founder_email},
        company={"name": company_name},
    )

    if deck and deck.filename:
        ext = os.path.splitext(deck.filename)[1].lower()
        if ext not in _ALLOWED_EXT:
            raise HTTPException(400, f"Unsupported deck format {ext} (pdf/pptx/docx).")
        os.makedirs(_UPLOAD_DIR, exist_ok=True)
        path = os.path.join(_UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
        with open(path, "wb") as fh:
            fh.write(await deck.read())
        try:
            parsed = DeckConnector().fetch(file_path=path)
            # Deck extraction fills identity/company; explicit form fields win.
            bundle.signals = parsed.signals
            bundle.identity = {**parsed.identity, **{k: v for k, v in bundle.identity.items() if v}}
            bundle.company = {**parsed.company, "name": company_name}
        except Exception as exc:  # parse failure must not lose the application
            logger.warning("Deck parse failed: %s", exc)
            warnings.append("Deck could not be parsed automatically — routed to review.")

    result = IngestionService(db).ingest_bundle(bundle, channel="inbound")

    # Attach the founder-supplied profile now that entity resolution has told us
    # which founder this application belongs to. Profile problems degrade to a
    # warning — a rejected photo must never cost the founder their application.
    founder = MemoryRepository(db).get_founder(result.founder_id)
    if founder is not None:
        profile_fields = {
            "headline": founder_headline,
            "bio": founder_bio,
            "role": founder_role,
            "location": founder_location,
            "linkedin_url": founder_linkedin,
        }
        supplied = {k: v for k, v in profile_fields.items() if v}
        if supplied:
            try:
                profile_service.update_profile(founder, supplied, db)
            except ProfileError as exc:
                warnings.append(f"Profile details not saved: {exc}")

        if founder_photo and founder_photo.filename:
            try:
                profile_service.save_photo(
                    founder, await founder_photo.read(), founder_photo.content_type, db
                )
            except ProfileError as exc:
                warnings.append(f"Photo not saved: {exc}")

    screening = first_pass(result.application_id, db)

    return {
        "application_id": result.application_id,
        "founder_id": result.founder_id,
        "founder_name": result.founder_name,
        "dedup_action": result.dedup_action,
        "signals_extracted": result.signals_added,
        "screening": {
            "decision": screening.decision,
            "reason": screening.reason,
            "thesis_fit": screening.thesis_fit,
        },
        "warnings": warnings + result.warnings,
    }


@router.get("/{application_id}")
def get_application(application_id: int, db: Session = Depends(get_db)) -> dict:
    """Return an application with its screening result and axis scores."""
    repo = MemoryRepository(db)
    app = repo.get_application(application_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    company = repo.get_company(app.company_id)
    return {
        "id": app.id,
        "founder_id": app.founder_id,
        "company_name": company.name,
        "channel": app.channel,
        "stage": app.stage,
        "screening_decision": app.screening_decision,
        "screening_reason": app.screening_reason,
        "axes": {
            axis: {"value": row.value, "trend": row.trend, "rationale": row.rationale}
            for axis, row in repo.latest_axis_scores(application_id).items()
        },
    }
