"""Investment memo endpoints (FR-8, FR-9, Epic G/F).

Generates decision-ready memos with inline evidence, contradiction flags, and
explicit gap disclosure. Missing data is flagged, never fabricated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.memo_service import MemoService

router = APIRouter()


@router.post("/generate/{opportunity_id}")
def generate_memo(opportunity_id: int, db: Session = Depends(get_db)) -> dict:
    """Generate a memo: required sections + adversarial view + Trust Score + evidence."""
    try:
        memo_id = MemoService(db).generate(opportunity_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return MemoService(db).get_full(memo_id)


@router.get("/{memo_id}")
def get_memo(memo_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a memo with claims linked to Evidence rows (confidence tiers)."""
    try:
        return MemoService(db).get_full(memo_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
