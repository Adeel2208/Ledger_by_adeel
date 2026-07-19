"""Sourcing service — outbound discovery + activation (FR-5, Epic D).

Activation (D3) is the step that turns a passive watchlist into a real pipeline:
a discovered founder (scanned from GitHub/arXiv/etc., no application yet) is
converted into an Application on the OUTBOUND channel and dropped into the exact
same screening funnel as inbound applicants — channel is recorded for analytics
but never fed to any scorer (D2 consistency guarantee).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence.screening import first_pass
from app.memory.repository import MemoryRepository
from app.models.application import Application
from app.models.founder import Founder
from app.models.outreach import Outreach


def discovered_founders(db: Session) -> list[dict]:
    """Founders in Memory with no application yet — the outbound watchlist."""
    repo = MemoryRepository(db)
    with_apps = select(Application.founder_id)
    founders = db.scalars(
        select(Founder).where(~Founder.id.in_(with_apps)).order_by(Founder.created_at.desc())
    )
    rows = []
    for f in founders:
        latest = repo.latest_score(f.id)
        rows.append(
            {
                "founder_id": f.id,
                "name": f.name,
                "github_handle": f.github_handle,
                "is_cold_start": f.is_cold_start,
                "founder_score": latest.value if latest else None,
                "momentum": latest.momentum if latest else None,
                "signal_count": len(repo.signals_for(f.id)),
            }
        )
    return rows


def activate_founder(founder_id: int, company: dict, db: Session) -> dict:
    """Convert a discovered founder into a real application (outbound channel).

    Records the outreach as activated, creates the opportunity, and immediately
    runs the same first-pass screening inbound applications get.
    """
    repo = MemoryRepository(db)
    founder = repo.get_founder(founder_id)
    if founder is None:
        raise ValueError(f"Founder {founder_id} not found")

    comp = repo.create_company(company)
    application = repo.create_application(founder_id, comp.id, channel="outbound")
    db.add(Outreach(founder_id=founder_id, channel="email", status="activated"))
    db.commit()

    screening = first_pass(application.id, db)
    return {
        "application_id": application.id,
        "founder_id": founder_id,
        "founder_name": founder.name,
        "company_name": comp.name,
        "channel": "outbound",
        "screening": {
            "decision": screening.decision,
            "reason": screening.reason,
            "thesis_fit": screening.thesis_fit,
        },
    }
