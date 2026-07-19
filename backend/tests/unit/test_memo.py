"""Memo + Trust guardrails: evidence linkage, contradiction flagging, honest gaps.

Runs fully offline with a fake LLM that returns structured memo/contradiction data.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.trust.evidence_tracer import compute_trust_score, reconcile_claim_confidence
from app.memory.ingestion.base import IngestBundle, RawSignal
from app.schemas.common import Confidence
from app.schemas.memo import (
    Contradiction,
    Contradictions,
    MemoClaim,
    MemoLLM,
    MemoSectionLLM,
)
from app.services.ingestion_service import IngestionService
from app.services.memo_service import MemoService


def _section(summary, claims=None):
    return MemoSectionLLM(title="s", summary=summary, claims=claims or [])


class FakeMemoLLM:
    """Cites `evidence_id` in one claim and reports a contradiction between two signals."""

    def __init__(self, evidence_id, contra_pair=None):
        self.evidence_id = evidence_id
        self.contra_pair = contra_pair

    def structured(self, prompt, schema, *, system=None, temperature=0.0, fast=False):
        if schema is Contradictions:
            items = []
            if self.contra_pair:
                items = [Contradiction(signal_id_a=self.contra_pair[0], signal_id_b=self.contra_pair[1],
                                       description="claimed metric vs independent source", severity="high")]
            return Contradictions(contradictions=items)
        if schema is MemoLLM:
            claim = MemoClaim(text="Backed claim", evidence_signal_ids=[self.evidence_id],
                              confidence=Confidence.VERIFIED)
            return MemoLLM(
                company_snapshot=_section("snap", [claim]),
                investment_hypotheses=_section("hyp"),
                swot=_section("swot"),
                problem_and_product=_section("prob"),
                traction_and_kpis=_section("traction"),
                adversarial_view=_section("risks"),
                disclosed_gaps=["Cap table: not disclosed"],
                recommendation="need_more_info",
                recommendation_rationale="thin data",
            )
        raise AssertionError(f"unexpected schema {schema}")


def _seed(db, confidence=Confidence.VERIFIED):
    res = IngestionService(db).ingest_bundle(
        IngestBundle(
            identity={"name": "F"},
            company={"name": "Co", "sector": "AI", "stage": "seed"},
            signals=[
                RawSignal("github", "github_profile", {"text": "p"}, datetime.now(timezone.utc),
                          confidence, text="p"),
                RawSignal("deck", "traction_claim", {"text": "claims $120k MRR"},
                          datetime.now(timezone.utc), Confidence.CLAIMED, text="claims $120k MRR"),
            ],
        ),
        index=False,
    )
    from app.memory.repository import MemoryRepository

    sigs = MemoryRepository(db).signals_for(res.founder_id)
    return res.application_id, sigs


def test_memo_has_required_sections_and_discloses_gaps(db_session):
    app_id, sigs = _seed(db_session)
    svc = MemoService(db_session, llm=FakeMemoLLM(evidence_id=sigs[0].id), validate=False)
    memo = svc.get_full(svc.generate(app_id))

    titles = {s["title"] for s in memo["sections"]}
    assert {"Company Snapshot", "Investment Hypotheses", "SWOT", "Problem & Product",
            "Traction & KPIs", "Adversarial / Risk View"} <= titles
    # The gap is disclosed as an explicit gap section, never fabricated away.
    assert any(s["is_gap"] and "Cap table" in s["body"] for s in memo["sections"])


def test_claim_links_to_evidence_with_source(db_session):
    app_id, sigs = _seed(db_session)
    svc = MemoService(db_session, llm=FakeMemoLLM(evidence_id=sigs[0].id), validate=False)
    memo = svc.get_full(svc.generate(app_id))
    snapshot = next(s for s in memo["sections"] if s["title"] == "Company Snapshot")
    ev = snapshot["claims"][0]["evidence"][0]
    assert ev["signal_id"] == sigs[0].id and ev["source"] == "github"


def test_contradiction_flags_affected_claim(db_session):
    app_id, sigs = _seed(db_session)
    # LLM cites the deck traction signal AND flags it as contradicting the github one.
    svc = MemoService(db_session, validate=False, llm=FakeMemoLLM(evidence_id=sigs[1].id,
                                                  contra_pair=(sigs[0].id, sigs[1].id)))
    memo = svc.get_full(svc.generate(app_id))
    snapshot = next(s for s in memo["sections"] if s["title"] == "Company Snapshot")
    assert snapshot["claims"][0]["contradicted"] is True


def test_unsupported_claim_cannot_be_verified():
    # A 'verified' claim with no evidence is downgraded — honesty by construction.
    assert reconcile_claim_confidence(Confidence.VERIFIED, []) == Confidence.CLAIMED
    # A claim can't outrank its evidence.
    assert reconcile_claim_confidence(Confidence.VERIFIED, ["claimed"]) == Confidence.CLAIMED
    # Backed by a verified source -> stays verified.
    assert reconcile_claim_confidence(Confidence.VERIFIED, ["verified"]) == Confidence.VERIFIED


def test_trust_score_penalizes_contradictions_and_gaps():
    strong = compute_trust_score(["verified", "verified"], [], 0)
    weak = compute_trust_score(
        ["claimed", "claimed"],
        [Contradiction(signal_id_a=1, signal_id_b=2, description="x", severity="high")],
        gap_count=3,
    )
    assert strong > weak
    assert 0 <= weak <= 100
