"""Scoring orchestration — produces the three INDEPENDENT axes and persists them.

Runs each axis scorer, derives per-axis trend from history, and stores an AxisScore
row per axis. Returns a `TripleScore` — three results side by side. There is no
code path here that averages them into a composite (hard non-negotiable, FR-6).

`llm` is injectable so the whole pipeline can be exercised offline with a fake
provider (see tests) without spending API credits.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.scoring.base import Axis, AxisResult, TripleScore
from app.intelligence.scoring.founder_axis import FounderAxisScorer
from app.intelligence.scoring.idea_axis import IdeaAxisScorer
from app.intelligence.scoring.market_axis import MarketAxisScorer
from app.intelligence.scoring.trend import compute_trend
from app.memory.repository import MemoryRepository


class ScoringService:
    def __init__(self, db: Session, llm=None) -> None:
        self.db = db
        self.repo = MemoryRepository(db)
        self._scorers = [
            FounderAxisScorer(db, llm),
            MarketAxisScorer(db, llm),
            IdeaAxisScorer(db, llm),
        ]

    def score(self, application_id: int) -> TripleScore:
        results: dict[Axis, AxisResult] = {}
        for scorer in self._scorers:
            axis = scorer.axis
            prev = self.repo.latest_axis_scores(application_id).get(axis.value)

            result = scorer.score(application_id)

            history = ([prev.value] if prev else []) + [result.value]
            result.trend = compute_trend(history)

            self.repo.add_axis_score(
                application_id,
                axis.value,
                result.value,
                result.trend.value,
                result.rationale,
                result.evidence_ids,
            )
            results[axis] = result

        self.db.commit()
        # Constructing TripleScore by named axis guarantees all three are present
        # and distinct — the type itself refuses to collapse them.
        return TripleScore(
            founder=results[Axis.FOUNDER],
            market=results[Axis.MARKET],
            idea=results[Axis.IDEA],
        )

    def current(self, application_id: int) -> dict:
        """Latest persisted score per axis (for the GET endpoint). Never a composite."""
        latest = self.repo.latest_axis_scores(application_id)
        return {
            axis: {
                "value": row.value,
                "trend": row.trend,
                "rationale": row.rationale,
                "evidence_ids": row.evidence_ids,
                "scored_at": row.scored_at.isoformat(),
            }
            for axis, row in latest.items()
        }
