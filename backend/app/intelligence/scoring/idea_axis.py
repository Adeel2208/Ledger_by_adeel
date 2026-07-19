"""Idea-vs-Market axis scorer (FR-6, E1).

Does the idea survive scrutiny as-is, or is the team strong enough to pivot?
Distinct from both the founder axis (who they are) and the market axis (is the
space attractive): this judges the *specific bet* and its adaptability.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.scoring.base import Axis, AxisResult, BaseAxisScorer, run_axis, signal_context
from app.memory.repository import MemoryRepository

_SYSTEM = (
    "You are a VC analyst scoring the IDEA-vs-MARKET axis only. Judge whether the "
    "specific idea survives scrutiny as-is, and if not, whether the evidence suggests a "
    "team able to pivot. Consider differentiation, problem urgency, and why-now. Score "
    "0-100, cite supporting signal IDs, and be explicit about assumptions and weaknesses."
)


class IdeaAxisScorer(BaseAxisScorer):
    axis = Axis.IDEA

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
        company = self.repo.get_company(app.company_id)
        signals = self.repo.signals_for(app.founder_id)
        prompt = (
            f"Company: {company.name} | sector={company.sector}\n\n"
            f"Evidence signals:\n{signal_context(signals)}\n\n"
            "Score the idea-vs-market axis 0-100 with rationale and cite supporting signal IDs."
        )
        return run_axis(
            self.llm,
            self.axis,
            system=_SYSTEM,
            prompt=prompt,
            valid_signal_ids={s.id for s in signals},
        )
