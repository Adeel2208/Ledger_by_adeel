"""Cold-start scoring method (FR-11, E3) — THE single most-flagged differentiator.

Explicit, documented alternate method for founders with no funding history, no
GitHub, and no network. Must NOT default to a low/no score. Scores from alternate
signals (public footprint, technical-artifact quality, direct problem-market-fit
reasoning) and produces a substantive Founder-axis score whose rationale is
DISTINCT from the track-record path — it never penalizes absence of traditional
signals, only rewards present alternate ones.

Full method + rubric: docs/COLD_START.md
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.scoring.base import Axis, AxisResult, run_axis, signal_context
from app.memory.repository import MemoryRepository

_SYSTEM = (
    "You are a VC analyst scoring a COLD-START founder — one with no funding history, "
    "no meaningful GitHub, and no network. You MUST NOT penalize the absence of those "
    "traditional signals. Instead judge capability from ALTERNATE evidence weighted "
    "equally: technical-artifact quality (demos, side projects), public footprint "
    "(writing, talks, community), self-taught trajectory, and the depth of their direct "
    "problem-market-fit reasoning. State explicitly that the cold-start method was used "
    "and which alternate signals drove the score. Cite supporting signal IDs."
)


class ColdStartScorer:
    axis = Axis.FOUNDER

    def __init__(self, db: Session, llm=None) -> None:
        self.repo = MemoryRepository(db)
        self._llm = llm

    @property
    def llm(self):
        if self._llm is None:
            from app.llm.client import get_llm

            self._llm = get_llm()
        return self._llm

    def score(self, application_id: int) -> AxisResult:
        app = self.repo.get_application(application_id)
        founder = self.repo.get_founder(app.founder_id)
        signals = self.repo.signals_for(founder.id)
        prompt = (
            f"Cold-start founder: {founder.name} (no funding/GitHub/network on record).\n\n"
            f"Alternate-signal evidence:\n{signal_context(signals)}\n\n"
            "Score the founder axis 0-100 using the cold-start method. Reward present "
            "alternate signals; do not deduct for missing traditional ones."
        )
        result = run_axis(
            self.llm,
            self.axis,
            system=_SYSTEM,
            prompt=prompt,
            valid_signal_ids={s.id for s in signals},
        )
        # Make the method visible in the rationale (Epic E3 acceptance).
        if "cold-start" not in result.rationale.lower():
            result.rationale = "[cold-start method] " + result.rationale
        return result
