"""Validator Agent (stretch I2) — cross-references claims against external web data.

For each founder-asserted claim, it pulls INDEPENDENT context from Tavily and asks
the LLM whether the external evidence supports, refutes, or can't confirm it. This
checks the primary scoring agent rather than trusting the deck blindly, and catches
seeded exaggerations in the demo. Degrades gracefully with no Tavily key.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.memory.ingestion.tavily import TavilyConnector
from app.memory.repository import MemoryRepository

# Claim record types worth externally validating (founder-asserted, not verified).
_VALIDATE_TYPES = {"traction_claim", "market_size", "team_background"}


class Verdict(BaseModel):
    verdict: str = Field(..., description="'supported' | 'refuted' | 'unconfirmed'")
    reasoning: str
    external_summary: str


def validate(application_id: int, db: Session, llm=None, max_claims: int = 3) -> list[dict]:
    repo = MemoryRepository(db)
    app = repo.get_application(application_id)
    company = repo.get_company(app.company_id)
    signals = [s for s in repo.signals_for(app.founder_id) if s.record_type in _VALIDATE_TYPES]
    if not signals:
        return []

    tavily = TavilyConnector()
    if llm is None:
        from app.llm.client import get_llm

        llm = get_llm()

    findings: list[dict] = []
    for sig in signals[:max_claims]:
        claim_text = (sig.payload or {}).get("text") or sig.record_type
        external = tavily.answer(f"{company.name} {company.sector}: {claim_text}")
        if not external:
            findings.append(
                {"signal_id": sig.id, "claim": claim_text, "verdict": "unconfirmed",
                 "reasoning": "No external data found.", "external_summary": ""}
            )
            continue
        result: Verdict = llm.structured(
            f"CLAIM (founder-asserted): {claim_text}\n\n"
            f"INDEPENDENT WEB EVIDENCE:\n{external}\n\n"
            "Does the external evidence support, refute, or fail to confirm the claim?",
            Verdict,
            system="You are a skeptical diligence validator. Be conservative: only 'supported' "
            "if the external evidence clearly backs the claim; 'refuted' if it conflicts.",
            fast=True,
        )
        findings.append(
            {"signal_id": sig.id, "claim": claim_text, "verdict": result.verdict,
             "reasoning": result.reasoning, "external_summary": result.external_summary}
        )
    return findings
