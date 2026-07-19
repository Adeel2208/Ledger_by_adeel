"""Multi-axis score endpoints (FR-6, Epic E).

Returns the three INDEPENDENT axes (founder / market / idea) with trend.
Never averaged into a single number (non-negotiable).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence.screening import first_pass
from app.services.scoring_service import ScoringService
from app.services.trace_service import TraceService

router = APIRouter()


@router.get("/{opportunity_id}/trace")
def get_trace(opportunity_id: int, db: Session = Depends(get_db)) -> dict:
    """Agentic Traceability (I1): the full reasoning chain, each step's conclusion
    resolved to the exact source artifacts that drove it."""
    try:
        return TraceService(db).build(opportunity_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{opportunity_id}/screen")
def screen(opportunity_id: int, db: Session = Depends(get_db)) -> dict:
    """Fast first-pass filter: pass | fail | review + stated reason."""
    try:
        result = first_pass(opportunity_id, db)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {
        "decision": result.decision,
        "reason": result.reason,
        "confidence": result.confidence,
        "thesis_fit": result.thesis_fit,
    }


@router.post("/{opportunity_id}/score")
def run_scoring(opportunity_id: int, db: Session = Depends(get_db)) -> dict:
    """Run the three independent axis scorers and persist the results."""
    if ScoringService(db).repo.get_application(opportunity_id) is None:
        raise HTTPException(404, "Opportunity not found")
    triple = ScoringService(db).score(opportunity_id)
    return {a.axis.value: _axis(a) for a in triple.as_list()}


@router.get("/{opportunity_id}/scores")
def get_scores(opportunity_id: int, db: Session = Depends(get_db)) -> dict:
    """Latest triple axis score + per-axis trend. No composite figure."""
    svc = ScoringService(db)
    if svc.repo.get_application(opportunity_id) is None:
        raise HTTPException(404, "Opportunity not found")
    return svc.current(opportunity_id)


def _axis(a) -> dict:
    return {
        "value": a.value,
        "trend": a.trend.value,
        "rationale": a.rationale,
        "evidence_ids": a.evidence_ids,
    }
