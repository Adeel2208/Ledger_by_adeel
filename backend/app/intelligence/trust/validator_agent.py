"""Validator Agent (stretch I2) — self-correction / anti-hallucination check.

For each founder-asserted claim, it cross-references the claim against TWO
independent sources of truth before trusting the primary agent:
  1. OBSERVABLE EVIDENCE — the founder's own independent, higher-confidence signals
     (verified/corroborated), e.g. an independent launch that cites real customer
     numbers. This catches a deck that inflates a metric its own footprint refutes.
  2. EXTERNAL DATA — live web context via Tavily (market reality, comparables).

The LLM returns supported / refuted / unconfirmed per claim. A `refuted` verdict is
what flags a seeded false/exaggerated claim in the demo. Degrades gracefully with
no Tavily key (falls back to observable-evidence-only validation).
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.memory.ingestion.tavily import TavilyConnector
from app.memory.repository import MemoryRepository
from app.schemas.common import Confidence

# Founder-asserted claim types worth externally validating (not already verified).
_VALIDATE_TYPES = {"traction_claim", "market_size", "team_background", "problem_statement"}
# Confidence tiers we treat as independent "observable evidence".
_OBSERVABLE = {Confidence.VERIFIED.value, Confidence.CORROBORATED.value}


class Verdict(BaseModel):
    verdict: str = Field(..., description="'supported' | 'refuted' | 'unconfirmed'")
    reasoning: str = Field(..., description="One sentence, referencing the evidence used.")


def validate(application_id: int, db: Session, llm=None, tavily=None, max_claims: int = 3) -> list[dict]:
    repo = MemoryRepository(db)
    app = repo.get_application(application_id)
    if app is None:
        return []
    company = repo.get_company(app.company_id)
    signals = repo.signals_for(app.founder_id)

    claims = [s for s in signals if s.record_type in _VALIDATE_TYPES]
    observable = [
        s for s in signals if s.confidence in _OBSERVABLE and s.record_type not in _VALIDATE_TYPES
    ]
    if not claims:
        return []

    if tavily is None:
        tavily = TavilyConnector()
    if llm is None:
        from app.llm.client import get_llm

        llm = get_llm()

    obs_text = "\n".join(
        f"- [{s.source}|{s.confidence}] {(s.payload or {}).get('text') or s.record_type}"
        for s in observable
    ) or "(none)"

    findings: list[dict] = []
    for sig in claims[:max_claims]:
        claim_text = (sig.payload or {}).get("text") or sig.record_type
        external = tavily.answer(f"{company.name} {company.sector or ''}: {claim_text}") or "(no external data found)"

        result: Verdict = llm.structured(
            f"FOUNDER-ASSERTED CLAIM: {claim_text}\n\n"
            f"OBSERVABLE EVIDENCE (the founder's own independent signals):\n{obs_text}\n\n"
            f"EXTERNAL WEB DATA:\n{external}\n\n"
            "Is the claim SUPPORTED, REFUTED, or UNCONFIRMED by the evidence above? "
            "Refute only when the evidence directly conflicts with the claim (e.g. a much "
            "smaller independently-observed number). Reference which evidence you used.",
            Verdict,
            system="You are a skeptical diligence validator whose job is to catch a primary "
            "agent hallucinating or over-trusting founder claims. Be conservative.",
            fast=True,
        )
        findings.append(
            {
                "signal_id": sig.id,
                "claim": claim_text,
                "verdict": result.verdict.lower().strip(),
                "reasoning": result.reasoning,
            }
        )
    return findings
