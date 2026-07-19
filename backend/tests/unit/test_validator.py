"""Validator Agent guardrail (I2): a false/exaggerated claim is caught (refuted).

Offline: fake LLM + fake Tavily (no network), so the whole flow is deterministic.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.trust.validator_agent import Verdict, validate
from app.memory.ingestion.base import IngestBundle, RawSignal
from app.schemas.common import Confidence
from app.services.ingestion_service import IngestionService


class FakeTavily:
    def answer(self, query):  # no external data for a fictional company
        return None


class FakeValidatorLLM:
    """Refutes a claim when observable evidence contains a much smaller number."""

    def structured(self, prompt, schema, *, system=None, temperature=0.0, fast=False):
        assert schema is Verdict
        # The deck claims 40,000; observable evidence says 15 -> refuted.
        if "40,000" in prompt and "15 paying teams" in prompt:
            return Verdict(verdict="refuted", reasoning="Independent evidence shows only 15 teams.")
        return Verdict(verdict="unconfirmed", reasoning="No conclusive evidence.")


def test_validator_refutes_inflated_claim(db_session):
    res = IngestionService(db_session).ingest_bundle(
        IngestBundle(
            identity={"name": "Max"},
            company={"name": "PayPlex", "sector": "FinTech", "stage": "seed"},
            signals=[
                RawSignal("deck", "traction_claim",
                          {"text": "Deck claims 40,000 paying customers as of Q2."},
                          datetime.now(timezone.utc), Confidence.CLAIMED, text="Deck claims 40,000 paying customers as of Q2."),
                RawSignal("producthunt", "product_launch",
                          {"text": "Independent launch; comments cite exactly 15 paying teams."},
                          datetime.now(timezone.utc), Confidence.CORROBORATED, text="Independent launch; comments cite exactly 15 paying teams."),
            ],
        ),
        index=False,
    )
    findings = validate(res.application_id, db_session, llm=FakeValidatorLLM(), tavily=FakeTavily())
    assert any(f["verdict"] == "refuted" for f in findings)
