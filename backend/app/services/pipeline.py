"""The deal pipeline state machine: Sourcing -> Screening -> Diligence -> Decision.

Owns cross-layer orchestration so routers stay thin and layers stay decoupled.
Inbound and outbound CONVERGE before Screening, guaranteeing identical treatment.
"""
from __future__ import annotations

from enum import Enum


class Stage(str, Enum):
    SOURCED = "sourced"
    SCREENING = "screening"
    DILIGENCE = "diligence"
    DECISION = "decision"


def advance(opportunity_id: int) -> Stage:
    """Move an opportunity to its next stage, running that stage's work."""
    raise NotImplementedError
