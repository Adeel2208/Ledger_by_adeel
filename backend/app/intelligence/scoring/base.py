"""Multi-axis scoring contract (FR-6, Epic E).

The three axes are INDEPENDENT and NON-AVERAGED. This is a hard non-negotiable:
`TripleScore` deliberately exposes no `.overall`/`.average` — there is no code
path that collapses the axes into one number. The UI shows all three separately.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Trend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class Axis(str, Enum):
    FOUNDER = "founder"
    MARKET = "market"
    IDEA = "idea"          # idea-vs-market


@dataclass
class AxisResult:
    axis: Axis
    value: int                     # 0-100 for founder/idea; market may map bull/neutral/bear
    trend: Trend
    rationale: str                 # human-readable "why", drawn from evidence
    evidence_ids: list[int]        # links back to Evidence rows (traceability)


@dataclass
class TripleScore:
    """The three axes, side by side. Intentionally has NO composite accessor."""

    founder: AxisResult
    market: AxisResult
    idea: AxisResult

    def as_list(self) -> list[AxisResult]:
        return [self.founder, self.market, self.idea]


class BaseAxisScorer(ABC):
    axis: Axis

    @abstractmethod
    def score(self, application_id: int) -> AxisResult:
        """Produce this axis's independent score with trend + evidence links."""


# ── Shared helpers for LLM-backed axis scorers ────────────────────────────────
def signal_context(signals: list) -> str:
    """Render signals as an ID-tagged list the LLM can cite by `signal <id>`."""
    lines = []
    for s in signals:
        text = (s.payload or {}).get("text") or s.record_type
        lines.append(
            f"signal {s.id} [{s.source} | {s.record_type} | {s.confidence}]: {text}"
        )
    return "\n".join(lines) if lines else "(no signals available)"


def run_axis(
    llm,
    axis: "Axis",
    *,
    system: str,
    prompt: str,
    valid_signal_ids: set[int],
) -> AxisResult:
    """Call the LLM for a structured axis score and coerce it into an AxisResult.

    Evidence IDs are filtered to real signals so a hallucinated citation can't
    leak into the traceability chain. Trend is left STABLE here — the scoring
    service fills it from history.
    """
    from app.schemas.scoring import AxisScoreLLM

    out: AxisScoreLLM = llm.structured(prompt, AxisScoreLLM, system=system)
    evidence = [sid for sid in out.evidence_signal_ids if sid in valid_signal_ids]
    rationale = out.rationale
    if out.market_stance:  # keep the qualitative market call visible alongside 0-100
        rationale = f"[{out.market_stance}] {rationale}"
    return AxisResult(
        axis=axis,
        value=max(0, min(100, out.value)),
        trend=Trend.STABLE,
        rationale=rationale,
        evidence_ids=evidence,
    )
