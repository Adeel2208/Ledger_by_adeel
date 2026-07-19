"""Market axis scorer (FR-6, E1): sizing, competitors, SWOT -> bullish/neutral/bear.

Independent of the founder — a great founder in a dead market still scores the
market axis low. The qualitative stance (bullish/neutral/bear) is preserved on the
rationale so it isn't lost in the 0-100 projection.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.scoring.base import Axis, AxisResult, BaseAxisScorer, run_axis, signal_context
from app.memory.repository import MemoryRepository

_SYSTEM = (
    "You are a VC analyst scoring the MARKET axis only (ignore how good the founder is). "
    "Assess market size, growth, competition, and timing from the evidence and the "
    "company's sector/stage/geography. Return a 0-100 score AND a market_stance of "
    "'bullish', 'neutral', or 'bear'. Cite supporting signal IDs; flag if market data is thin."
)


class MarketAxisScorer(BaseAxisScorer):
    axis = Axis.MARKET

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
            f"Company: {company.name} | sector={company.sector} | stage={company.stage} "
            f"| geography={company.geography}\n\n"
            f"Evidence signals:\n{signal_context(signals)}\n\n"
            "Score the market axis 0-100, set market_stance, and cite supporting signal IDs."
        )
        result = run_axis(
            self.llm,
            self.axis,
            system=_SYSTEM,
            prompt=prompt,
            valid_signal_ids={s.id for s in signals},
        )
        return result
