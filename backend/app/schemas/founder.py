"""Founder / company DTOs + the LLM extraction schema.

`ExtractedProfile` is the structured target for LLM entity extraction from raw
sources (the 'Cognify' step of the ingestion pipeline): the model reads a deck /
GitHub blob / web page and returns identity + claims as validated JSON.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Confidence


# ── LLM extraction target (structured output) ─────────────────────────────────
class ExtractedClaim(BaseModel):
    """A single factual assertion the model found, with where it came from."""

    text: str = Field(..., description="The claim in one sentence, e.g. '£40k MRR as of Q2'.")
    record_type: str = Field(..., description="e.g. traction_claim, team_background, market_size")
    value: str | None = Field(None, description="Normalised value if quantitative, else null.")
    location: str | None = Field(None, description="Where in the source, e.g. 'slide 4'.")
    confidence: Confidence = Confidence.CLAIMED


class ExtractedProfile(BaseModel):
    """Identity + claims extracted from one raw source. Never invent fields —
    leave unknowns null so the honesty-over-completeness rule holds."""

    founder_name: str | None = None
    founder_email: str | None = None
    github_handle: str | None = None
    linkedin_url: str | None = None
    company_name: str | None = None
    sector: str | None = None
    stage: str | None = None
    geography: str | None = None
    claims: list[ExtractedClaim] = Field(default_factory=list)


# ── API DTOs ──────────────────────────────────────────────────────────────────
class FounderScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: float
    momentum: str | None
    components: dict
    computed_at: datetime


class FounderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    github_handle: str | None
    is_cold_start: bool
    # Latest persistent score (may be None before first computation).
    founder_score: float | None = None
    momentum: str | None = None
