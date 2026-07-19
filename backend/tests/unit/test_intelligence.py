"""Intelligence-layer guardrails: thesis fit, screening, and the three axes.

The axis scorers are exercised with a FAKE LLM (injected) so the full scoring
pipeline runs offline and deterministically — no API key, no network.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.scoring.base import TripleScore
from app.intelligence.scoring.trend import compute_trend
from app.intelligence.screening import first_pass
from app.intelligence.thesis_engine import score_company
from app.memory.ingestion.base import IngestBundle, RawSignal
from app.models.thesis import Thesis
from app.schemas.common import Confidence
from app.schemas.scoring import AxisScoreLLM
from app.services.ingestion_service import IngestionService
from app.services.scoring_service import ScoringService


class FakeLLM:
    """Returns a fixed structured score; records that a founder-axis call happened."""

    def __init__(self, value=70, stance="neutral"):
        self.value = value
        self.stance = stance
        self.prompts: list[str] = []

    def structured(self, prompt, schema, *, system=None, temperature=0.0, fast=False):
        self.prompts.append(prompt)
        return AxisScoreLLM(
            value=self.value,
            rationale="fake rationale",
            evidence_signal_ids=[],
            market_stance=self.stance,
        )


def _seed_opportunity(db, *, is_cold_start=False, sector="AI"):
    thesis = Thesis(name="t", sectors=["AI"], stages=["seed"], geographies=[], is_active=True)
    db.add(thesis)
    db.commit()
    res = IngestionService(db).ingest_bundle(
        IngestBundle(
            identity={"name": "Test Founder"},
            company={"name": "Co", "sector": sector, "stage": "seed", "geography": "Berlin"},
            signals=[
                RawSignal("github", "github_profile", {"text": "profile"},
                          datetime.now(timezone.utc), Confidence.VERIFIED, text="profile"),
            ],
        ),
        is_cold_start=is_cold_start,
        index=False,
    )
    return res.application_id


def test_thesis_fit_is_explainable_and_bounded(db_session):
    thesis = Thesis(sectors=["AI"], stages=["seed"], geographies=["Berlin"])

    class C:  # lightweight stand-in for a Company row
        sector, stage, geography = "AI", "seed", "Berlin"

    fit = score_company(C(), thesis)
    assert fit.score == 100 and fit.reasons  # all dims match, reasons present

    class C2:
        sector, stage, geography = "Biotech", "series-a", "Tokyo"

    assert score_company(C2(), thesis).score == 0


def test_screening_passes_in_thesis_and_flags_out_of_thesis(db_session):
    in_thesis = _seed_opportunity(db_session, sector="AI")
    assert first_pass(in_thesis, db_session).decision == "pass"

    out_thesis = _seed_opportunity(db_session, sector="Cannabis")
    assert first_pass(out_thesis, db_session).decision in ("fail", "review")


def test_triple_score_returns_three_independent_axes(db_session):
    app_id = _seed_opportunity(db_session)
    triple = ScoringService(db_session, llm=FakeLLM(value=70)).score(app_id)
    assert isinstance(triple, TripleScore)
    axes = {a.axis.value for a in triple.as_list()}
    assert axes == {"founder", "market", "idea"}
    # No composite accessor exists — the three are separately addressable.
    assert not hasattr(triple, "overall")


def test_cold_start_founder_routes_through_alternate_method(db_session):
    app_id = _seed_opportunity(db_session, is_cold_start=True)
    fake = FakeLLM(value=55)
    triple = ScoringService(db_session, llm=fake).score(app_id)
    # Cold-start method tags its rationale explicitly (Epic E3 acceptance).
    assert "cold-start" in triple.founder.rationale.lower()


def test_trend_from_history():
    assert compute_trend([50, 60]).value == "improving"
    assert compute_trend([60, 50]).value == "declining"
    assert compute_trend([50, 51]).value == "stable"
    assert compute_trend([50]).value == "stable"
