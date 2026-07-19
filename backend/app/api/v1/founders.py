"""Founder endpoints (FR-7, Epic B).

Exposes the persistent Founder Score + history that follows a person across
applications and never resets.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.memory.enrichment import assess
from app.memory.repository import MemoryRepository

router = APIRouter()


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
    }
