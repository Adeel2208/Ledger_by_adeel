"""Ingestion connector contract.

Every source (deck, GitHub, arXiv, ProductHunt, web) implements `BaseConnector`.
Connectors are the ONLY producers of `Signal` records, and every Signal they emit
must carry source + timestamp + confidence + record_type (Requirements FR-2, B1).

A connector's job is the 'Extract' step: turn a raw source into `RawSignal`s.
Identity resolution, LLM claim-extraction, embedding, and persistence happen
downstream in the ingestion service — connectors stay thin and testable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.schemas.common import Confidence


@dataclass
class RawSignal:
    """A single evidence-bearing data point, pre-persistence.

    `confidence` reflects source reliability tier (see schemas.common.Confidence):
        verified > corroborated > claimed > scraped
    Never invent values — missing fields stay missing (honesty-over-completeness).
    """

    source: str                 # e.g. "github", "deck:slide-4", "arxiv"
    record_type: str            # e.g. "commit_activity", "traction_claim", "paper"
    payload: dict[str, Any]
    timestamp: datetime
    confidence: Confidence = Confidence.CLAIMED
    external_url: str | None = None       # for evidence tracing / agentic traceability
    text: str | None = None               # human-readable form used for embedding/search
    # Identity hints this source revealed, used by dedup to attach to the right founder.
    identity: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestBundle:
    """What a connector returns: the founder/company identity it observed plus signals."""

    signals: list[RawSignal]
    identity: dict[str, Any] = field(default_factory=dict)   # name/email/github_handle/...
    company: dict[str, Any] = field(default_factory=dict)    # name/sector/stage/geography


class BaseConnector(ABC):
    name: str

    @abstractmethod
    def fetch(self, **kwargs: Any) -> IngestBundle:
        """Pull signals from this source. Must not raise on missing data — omit it."""
