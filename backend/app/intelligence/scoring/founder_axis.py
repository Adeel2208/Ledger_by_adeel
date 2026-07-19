"""Founder axis scorer (FR-6, E1).

Scores who the founder is: traits, track record, execution ability. Pulls the
persistent Founder Score (memory/founder_score.py) as ONE input among several —
not a replacement. Routes no-history founders to the cold-start method so absence
of GitHub/funding never means a default-low score.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.scoring.base import Axis, AxisResult, BaseAxisScorer, run_axis, signal_context
from app.intelligence.scoring.cold_start import ColdStartScorer
from app.memory.repository import MemoryRepository

_SYSTEM = (
    "You are a VC analyst scoring the FOUNDER axis only (not the market or the idea). "
    "Judge capability from evidence: technical depth, execution, communication, "
    "resilience. Treat the persistent Founder Score as one prior input, not the answer. "
    "Cite the signal IDs that drive your score. Do not reward unverifiable claims."
)


class FounderAxisScorer(BaseAxisScorer):
    axis = Axis.FOUNDER

    def __init__(self, db: Session, llm=None) -> None:
        self.db = db
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

        # Cold-start founders use the documented alternate rubric (E3).
        if founder.is_cold_start:
            return ColdStartScorer(self.db, self._llm).score(application_id)

        signals = self.repo.signals_for(founder.id)
        persistent = self.repo.latest_score(founder.id)
        prior = (
            f"Persistent Founder Score: {persistent.value}/100, components={persistent.components}"
            if persistent
            else "Persistent Founder Score: none yet"
        )
        prompt = (
            f"Founder: {founder.name}\n{prior}\n\n"
            f"Evidence signals:\n{signal_context(signals)}\n\n"
            "Score the founder axis 0-100 with a rationale and cite supporting signal IDs."
        )
        return run_axis(
            self.llm,
            self.axis,
            system=_SYSTEM,
            prompt=prompt,
            valid_signal_ids={s.id for s in signals},
        )
