"""Investor dashboard endpoints (FR-10, Epic H).

Ranked opportunity list with momentum trend. Notion-simple, Bloomberg-deep.
Returns one row per opportunity joining founder + company + the three independent
axis scores + thesis fit + persistent founder score. The three axes travel
separately — the row never contains a blended composite.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence.thesis_engine import score_thesis_fit
from app.memory.repository import MemoryRepository

router = APIRouter()


@router.get("")
def get_dashboard(db: Session = Depends(get_db)) -> dict:
    """Ranked founder/opportunity list, each with three axis scores + trend."""
    repo = MemoryRepository(db)
    rows = []
    for app in repo.list_applications():
        founder = repo.get_founder(app.founder_id)
        company = repo.get_company(app.company_id)
        axes = repo.latest_axis_scores(app.id)
        fscore = repo.latest_score(founder.id)
        fit = score_thesis_fit(company, db)
        memo = repo.latest_memo_for(app.id)

        rows.append(
            {
                "application_id": app.id,
                "founder_id": founder.id,
                "founder_name": founder.name,
                "company_name": company.name,
                "sector": company.sector,
                "stage": company.stage,
                "geography": company.geography,
                "channel": app.channel,
                "is_cold_start": founder.is_cold_start,
                "screening_decision": app.screening_decision,
                "thesis_fit": fit.score,
                "founder_score": fscore.value if fscore else None,
                "momentum": fscore.momentum if fscore else None,
                # Three INDEPENDENT axes — never averaged.
                "axes": {
                    axis: {"value": row.value, "trend": row.trend}
                    for axis, row in axes.items()
                },
                "has_memo": memo is not None,
                "memo_id": memo.id if memo else None,
                "recommendation": memo.recommendation if memo else None,
                "trust_score": memo.trust_score if memo else None,
            }
        )

    # Rank by thesis fit, then by whether they've been scored (scored first).
    rows.sort(key=lambda r: (r["thesis_fit"], len(r["axes"])), reverse=True)
    return {"opportunities": rows, "count": len(rows)}
