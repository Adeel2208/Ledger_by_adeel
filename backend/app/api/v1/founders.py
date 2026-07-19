"""Founder endpoints (FR-7, Epic B).

Exposes the persistent Founder Score + history that follows a person across
applications and never resets.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.memory.enrichment import assess
from app.memory.repository import MemoryRepository
from app.services import profile_service
from app.services.profile_service import ProfileError

router = APIRouter()


def _profile_block(founder) -> dict:
    """The presentation-ready identity block shared by list and detail views."""
    mono = profile_service.monogram(founder)
    return {
        "photo_url": (
            "/media/" + founder.photo_path.replace("\\", "/") if founder.photo_path else None
        ),
        "monogram": {"initials": mono.initials, "color": mono.color},
        "headline": founder.headline,
        "bio": founder.bio,
        "role": founder.role,
        "location": founder.location,
        "personal_url": founder.personal_url,
        "twitter_handle": founder.twitter_handle,
        "linkedin_url": founder.linkedin_url,
        "work_history": founder.work_history or [],
        "profile_updated_at": (
            founder.profile_updated_at.isoformat() if founder.profile_updated_at else None
        ),
        "completeness": profile_service.completeness(founder),
    }


@router.get("")
def list_founders(db: Session = Depends(get_db)) -> list[dict]:
    """List founders with their latest persistent score and momentum."""
    repo = MemoryRepository(db)
    out = []
    for f in repo.list_founders():
        latest = repo.latest_score(f.id)
        out.append(
            {
                "id": f.id,
                "name": f.name,
                "github_handle": f.github_handle,
                "is_cold_start": f.is_cold_start,
                "founder_score": latest.value if latest else None,
                "momentum": latest.momentum if latest else None,
                # Avatar + headline so list views render a face, not just a row.
                "profile": _profile_block(f),
            }
        )
    return out


@router.get("/{founder_id}")
def get_founder(founder_id: int, db: Session = Depends(get_db)) -> dict:
    """Founder profile: persistent score, trajectory, signals, and data coverage."""
    repo = MemoryRepository(db)
    founder = repo.get_founder(founder_id)
    if founder is None:
        raise HTTPException(404, "Founder not found")

    history = repo.score_history(founder_id)
    latest = history[-1] if history else None
    return {
        "id": founder.id,
        "name": founder.name,
        "email": founder.email,
        "github_handle": founder.github_handle,
        "linkedin_url": founder.linkedin_url,
        "is_cold_start": founder.is_cold_start,
        "founder_score": latest.value if latest else None,
        "momentum": latest.momentum if latest else None,
        "components": latest.components if latest else {},
        "score_history": [
            {"value": s.value, "momentum": s.momentum, "computed_at": s.computed_at.isoformat()}
            for s in history
        ],
        "signals": [
            {
                "id": s.id,
                "source": s.source,
                "record_type": s.record_type,
                "confidence": s.confidence,
                "external_url": s.external_url,
                "timestamp": s.source_timestamp.isoformat(),
                "payload": s.payload,
            }
            for s in repo.signals_for(founder_id)
        ],
        "data_quality": assess(founder_id, db),
        "profile": _profile_block(founder),
    }


@router.patch("/{founder_id}/profile")
def update_founder_profile(
    founder_id: int, fields: dict = Body(...), db: Session = Depends(get_db)
) -> dict:
    """Update founder-supplied profile details (partial; unknown keys ignored)."""
    founder = MemoryRepository(db).get_founder(founder_id)
    if founder is None:
        raise HTTPException(404, "Founder not found")
    try:
        profile_service.update_profile(founder, fields, db)
    except ProfileError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _profile_block(founder)


@router.post("/{founder_id}/photo")
async def upload_founder_photo(
    founder_id: int, photo: UploadFile = File(...), db: Session = Depends(get_db)
) -> dict:
    """Accept a founder-supplied photo (JPEG/PNG/WebP), normalised and EXIF-stripped."""
    founder = MemoryRepository(db).get_founder(founder_id)
    if founder is None:
        raise HTTPException(404, "Founder not found")
    try:
        profile_service.save_photo(founder, await photo.read(), photo.content_type, db)
    except ProfileError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _profile_block(founder)
