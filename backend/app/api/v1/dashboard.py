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
from app.services import profile_service

router = APIRouter()


def _hours_between(start, end) -> float | None:
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 3600, 1)


@router.get("")
def get_dashboard(db: Session = Depends(get_db)) -> dict:
    """Ranked founder/opportunity list, each with three axis scores + trend."""
    repo = MemoryRepository(db)
    rows = []
    decision_hours_all: list[float] = []
    for app in repo.list_applications():
        founder = repo.get_founder(app.founder_id)
        company = repo.get_company(app.company_id)
        axes = repo.latest_axis_scores(app.id)
        fscore = repo.latest_score(founder.id)
        fit = score_thesis_fit(company, db)
        memo = repo.latest_memo_for(app.id)

        # Velocity: first-signal-to-decision (the brief's own yardstick).
        # "First signal" = the earliest moment the system knew about this
        # founder (earliest signal ingest, or the application itself if that
        # came first); "decision" = the memo carrying the recommendation.
        signals = repo.signals_for(founder.id)
        first_seen = min(
            [s.ingested_at for s in signals if s.ingested_at] + [app.created_at],
            default=app.created_at,
        )
        decision_hours = _hours_between(first_seen, memo.created_at if memo else None)
        if decision_hours is not None and decision_hours >= 0:
            decision_hours_all.append(decision_hours)

        rows.append(
            {
                "application_id": app.id,
                "founder_id": founder.id,
                "founder_name": founder.name,
                # Compact avatar block — photo if supplied, else the same
                # deterministic monogram the profile page uses. Deliberately
                # not the full profile: a ranked table doesn't need bios.
                "avatar": profile_service.avatar_block(founder),
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
                "decision_hours": decision_hours,
            }
        )

    # Rank by thesis fit, then by whether they've been scored (scored first).
    rows.sort(key=lambda r: (r["thesis_fit"], len(r["axes"])), reverse=True)

    # Fund-level velocity. Median (not mean) so one slow outlier doesn't drown
    # the story; within-24h rate is the brief's explicit target.
    decision_hours_all.sort()
    n = len(decision_hours_all)
    velocity = {
        "decided_count": n,
        "median_hours_to_decision": (
            round(
                (
                    decision_hours_all[n // 2]
                    if n % 2
                    else (decision_hours_all[n // 2 - 1] + decision_hours_all[n // 2]) / 2
                ),
                1,
            )
            if n
            else None
        ),
        "within_24h_rate": round(sum(1 for h in decision_hours_all if h <= 24) / n, 2) if n else None,
    }
    return {"opportunities": rows, "count": len(rows), "velocity": velocity}
