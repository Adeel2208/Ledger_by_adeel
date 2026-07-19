"""Outbound sourcing guardrails: watchlist + activation converge into the funnel (D1/D3)."""
from __future__ import annotations

from datetime import datetime, timezone

from app.memory.ingestion.base import IngestBundle, RawSignal
from app.models.thesis import Thesis
from app.schemas.common import Confidence
from app.services.ingestion_service import IngestionService
from app.services.sourcing_service import activate_founder, discovered_founders


def _discover(db):
    """Ingest a founder with signals but NO company -> watchlist, no application."""
    return IngestionService(db).ingest_bundle(
        IngestBundle(
            identity={"name": "Leo Test", "github_handle": "leotest"},
            company={},
            signals=[
                RawSignal("github", "github_profile", {"text": "profile"},
                          datetime.now(timezone.utc), Confidence.VERIFIED, text="profile"),
            ],
        ),
        channel="outbound",
        index=False,
    )


def test_discovered_founder_has_no_application_until_activated(db_session):
    res = _discover(db_session)
    assert res.application_id is None  # discovery alone creates no opportunity

    watchlist = discovered_founders(db_session)
    assert any(r["founder_id"] == res.founder_id for r in watchlist)
    # Persistent score already computed at discovery time (scored like inbound, D2).
    assert next(r for r in watchlist if r["founder_id"] == res.founder_id)["founder_score"] is not None


def test_activation_converges_into_screening_funnel(db_session):
    db_session.add(Thesis(sectors=["AI"], stages=["seed"], geographies=[], is_active=True))
    db_session.commit()
    res = _discover(db_session)

    out = activate_founder(
        res.founder_id, {"name": "EvalCo", "sector": "AI", "stage": "seed"}, db_session
    )
    # Activation produced a real application on the outbound channel...
    assert out["application_id"] is not None and out["channel"] == "outbound"
    # ...and it went through the SAME first-pass screening as inbound (D2/D3).
    assert out["screening"]["decision"] in ("pass", "review", "fail")
    assert out["screening"]["reason"]

    # Founder is no longer on the watchlist.
    assert all(r["founder_id"] != res.founder_id for r in discovered_founders(db_session))
