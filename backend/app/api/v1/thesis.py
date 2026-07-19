"""Thesis Engine endpoints (FR-1, Epic A).

Runtime-configurable investment thesis applied identically to inbound & outbound.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence.thesis_engine import get_active_thesis
from app.models.thesis import Thesis

router = APIRouter()


class ThesisIn(BaseModel):
    sectors: list[str] = []
    stages: list[str] = []
    geographies: list[str] = []
    check_size_min: int | None = None
    check_size_max: int | None = None
    ownership_target: float | None = None
    risk_appetite: str = "moderate"


def _serialize(t: Thesis) -> dict:
    return {
        "id": t.id,
        "sectors": t.sectors,
        "stages": t.stages,
        "geographies": t.geographies,
        "check_size_min": t.check_size_min,
        "check_size_max": t.check_size_max,
        "ownership_target": t.ownership_target,
        "risk_appetite": t.risk_appetite,
    }


@router.get("")
def get_thesis(db: Session = Depends(get_db)) -> dict | None:
    """Return the current active investment thesis."""
    t = get_active_thesis(db)
    return _serialize(t) if t else None


@router.put("")
def update_thesis(payload: ThesisIn, db: Session = Depends(get_db)) -> dict:
    """Replace the active thesis; changes re-rank the dashboard in real time (A1)."""
    # Deactivate previous theses, then activate the new one (keeps version history).
    for t in db.query(Thesis).filter(Thesis.is_active.is_(True)).all():
        t.is_active = False
    thesis = Thesis(is_active=True, **payload.model_dump())
    db.add(thesis)
    db.commit()
    db.refresh(thesis)
    return _serialize(thesis)
