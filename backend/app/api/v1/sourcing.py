"""Outbound sourcing + ingestion endpoints (FR-5, Epic D).

Discover founders before they fundraise, then *activate* them into the same
screening funnel as inbound applicants. Also the generic entry point for pulling
any source (github/arxiv/web/producthunt/tavily) into the Memory layer.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.memory.ingestion.registry import available_sources
from app.services.ingestion_service import IngestionService
from app.services.sourcing_service import activate_founder, discovered_founders

router = APIRouter()


class ScanRequest(BaseModel):
    source: str                       # github | arxiv | web | producthunt | tavily
    params: dict[str, Any] = {}       # e.g. {"username": "torvalds"} or {"url": "..."}
    is_cold_start: bool = False


class ActivateRequest(BaseModel):
    company_name: str
    sector: str | None = None
    stage: str | None = None
    geography: str | None = None


@router.get("/sources")
def sources() -> list[str]:
    """List registered ingestion sources."""
    return available_sources()


@router.get("/discovered")
def discovered(
    db: Session = Depends(get_db),
    include_intelligence: bool = True
) -> list[dict]:
    """
    Outbound watchlist: founders in Memory with no application yet (D1).
    
    Args:
        include_intelligence: If True, includes quality scores and activation recommendations
    
    Returns:
        List of discovered founders with intelligence scoring
    """
    return discovered_founders(db, include_intelligence=include_intelligence)


@router.get("/channel-analytics")
def get_channel_analytics(
    db: Session = Depends(get_db),
    lookback_days: int = 180
) -> dict:
    """
    Analyze sourcing channel performance.
    
    Returns:
    - Total discovered founders
    - Activation rate
    - Screening pass rate
    - Average signal quality
    - Recommendations for improvement
    """
    from app.services.sourcing_service import channel_performance_analytics
    
    return channel_performance_analytics(db, lookback_days=lookback_days)


@router.post("/scan")
def run_scan(req: ScanRequest, db: Session = Depends(get_db)) -> dict:
    """Pull one source into Memory: extract -> dedup -> persist -> index -> score."""
    result = IngestionService(db).ingest(
        req.source, is_cold_start=req.is_cold_start, channel="outbound", **req.params
    )
    return {
        "founder_id": result.founder_id,
        "founder_name": result.founder_name,
        "dedup_action": result.dedup_action,
        "dedup_reasons": result.dedup_reasons,
        "signals_added": result.signals_added,
        "needs_review": result.needs_review,
        "founder_score": result.founder_score,
        "application_id": result.application_id,
        "warnings": result.warnings,
    }


@router.post("/{founder_id}/activate")
def activate(founder_id: int, req: ActivateRequest, db: Session = Depends(get_db)) -> dict:
    """Convert a discovered founder into an application (converge with inbound funnel, D3)."""
    try:
        return activate_founder(
            founder_id,
            {
                "name": req.company_name,
                "sector": req.sector,
                "stage": req.stage,
                "geography": req.geography,
            },
            db,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
