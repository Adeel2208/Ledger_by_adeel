"""Structured LLM schemas for memo generation and contradiction detection.

The memo is generated as validated JSON (never free prose) so the UI renders it
programmatically and every claim can carry its own evidence + confidence. Required
sections are explicit fields so the five mandatory sections (FR-9) can never be
silently dropped. Missing data goes to `disclosed_gaps` — flagged, never invented.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Confidence


class MemoClaim(BaseModel):
    text: str = Field(..., description="A single factual assertion used in the memo.")
    evidence_signal_ids: list[int] = Field(
        default_factory=list, description="IDs of signals that back this claim. Empty if none."
    )
    confidence: Confidence = Field(
        Confidence.CLAIMED, description="Trust tier implied by the cited evidence."
    )


class MemoSectionLLM(BaseModel):
    title: str
    summary: str = Field(..., description="Concise prose. Do not pad; brevity is rewarded.")
    claims: list[MemoClaim] = Field(default_factory=list)


class MemoLLM(BaseModel):
    """The five REQUIRED sections (FR-9) as explicit fields + adversarial + decision."""

    company_snapshot: MemoSectionLLM
    investment_hypotheses: MemoSectionLLM
    swot: MemoSectionLLM
    problem_and_product: MemoSectionLLM
    traction_and_kpis: MemoSectionLLM
    adversarial_view: MemoSectionLLM = Field(..., description="The bear case / key risks (G3).")
    disclosed_gaps: list[str] = Field(
        default_factory=list,
        description="Data genuinely missing (e.g. 'Cap table: not disclosed'). Never fabricate.",
    )
    recommendation: str = Field(..., description="'invest' | 'pass' | 'need_more_info'")
    recommendation_rationale: str


# ── Contradiction detection ───────────────────────────────────────────────────
class Contradiction(BaseModel):
    signal_id_a: int
    signal_id_b: int
    description: str = Field(..., description="What conflicts between the two signals.")
    severity: str = Field("medium", description="'low' | 'medium' | 'high'")


class Contradictions(BaseModel):
    contradictions: list[Contradiction] = Field(default_factory=list)
