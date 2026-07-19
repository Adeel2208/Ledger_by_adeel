"""Structured LLM output schemas for the three scoring axes.

Every axis returns a value, a rationale, and the specific signal IDs that justify
it — so a score is never a black box and evidence can be traced (I1). Missing
support is allowed (empty evidence) but must be reflected in the rationale.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AxisScoreLLM(BaseModel):
    value: int = Field(..., ge=0, le=100, description="Axis score 0-100.")
    rationale: str = Field(..., description="Concise evidence-grounded justification.")
    evidence_signal_ids: list[int] = Field(
        default_factory=list, description="IDs of the signals that most support this score."
    )
    # Market axis only: qualitative stance. Null for other axes.
    market_stance: str | None = Field(
        None, description="For the market axis: 'bullish' | 'neutral' | 'bear'."
    )
