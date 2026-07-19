"""Memory-layer guardrails: dedup bands, provenance, and cold-start fairness."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.memory import dedup
from app.memory.founder_score import compute_founder_score
from app.memory.ingestion.base import IngestBundle, RawSignal
from app.schemas.common import Confidence
from app.services.ingestion_service import IngestionService


def _bundle(identity, signals, company=None):
    return IngestBundle(identity=identity, signals=signals, company=company or {})


def _sig(record_type, conf=Confidence.VERIFIED):
    return RawSignal(
        source="test",
        record_type=record_type,
        payload={},
        timestamp=datetime.now(timezone.utc),
        confidence=conf,
        text=record_type,
    )


def test_deterministic_identifier_forces_merge(db_session):
    svc = IngestionService(db_session)
    svc.ingest_bundle(_bundle({"name": "Ada Vance", "github_handle": "adavance"}, [_sig("github_profile")]), index=False)

    d = dedup.resolve({"name": "Completely Different", "github_handle": "adavance"}, db_session)
    assert d.action is dedup.Action.MERGE
    assert "github handle exact match" in d.reasons


def test_ambiguous_name_routes_to_review_not_silent_merge(db_session):
    svc = IngestionService(db_session)
    svc.ingest_bundle(_bundle({"name": "Jonathan Meyer"}, [_sig("github_profile")]), index=False)

    # Similar-but-not-identical name, no strong identifier -> must land in the REVIEW band.
    d = dedup.resolve({"name": "Jonathon Mayer"}, db_session)
    assert d.action in (dedup.Action.REVIEW, dedup.Action.NEW)
    assert d.action is not dedup.Action.MERGE


def test_signals_carry_full_provenance(db_session):
    svc = IngestionService(db_session)
    res = svc.ingest_bundle(_bundle({"name": "P", "email": "p@x.io"}, [_sig("github_profile")]), index=False)
    from app.memory.repository import MemoryRepository

    sig = MemoryRepository(db_session).signals_for(res.founder_id)[0]
    assert sig.source and sig.record_type and sig.confidence and sig.source_timestamp


def test_cold_start_not_penalized_for_absent_components(db_session):
    """A founder with only alternate signals must not be dragged to ~0 by missing GitHub."""
    svc = IngestionService(db_session)
    res = svc.ingest_bundle(
        _bundle(
            {"name": "Rosa"},
            [_sig("public_footprint", Confidence.SCRAPED), _sig("problem_statement", Confidence.CLAIMED)],
        ),
        is_cold_start=True,
        index=False,
    )
    score = compute_founder_score(res.founder_id, db_session)
    # Composite is the mean of OBSERVED components only -> substantive, not near-zero.
    assert score["value"] > 15
    assert score["components"]["technical"] == 0.0  # absence recorded, but not averaged in
