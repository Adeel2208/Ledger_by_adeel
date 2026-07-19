"""Fast first-pass filter (FR-4, C2).

Cheap pass/fail gate BEFORE full analysis: preliminary thesis alignment + basic
data-viability. Always returns a stated reason. Borderline cases route to a human
review queue rather than being silently dropped (never a false rejection).

Deterministic and cheap by design — this runs on every application to protect the
expensive multi-axis scoring from obvious non-starters.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.intelligence.thesis_engine import score_thesis_fit
from app.memory.repository import MemoryRepository

FAIL_BELOW = 25          # thesis fit under this -> clear non-starter
REVIEW_BELOW = 45        # marginal fit -> human review, never auto-reject


@dataclass
class ScreeningResult:
    decision: str        # pass | fail | review
    reason: str
    confidence: float    # 0-1
    thesis_fit: int = 0


def first_pass(application_id: int, db: Session) -> ScreeningResult:
    repo = MemoryRepository(db)
    app = repo.get_application(application_id)
    if app is None:
        raise ValueError(f"Application {application_id} not found")

    company = repo.get_company(app.company_id)
    fit = score_thesis_fit(company, db)
    signals = repo.signals_for(app.founder_id)

    if fit.score < FAIL_BELOW:
        result = ScreeningResult(
            "fail",
            f"Outside investment thesis (fit {fit.score}/100). " + "; ".join(fit.reasons[:2]),
            confidence=min(1.0, (FAIL_BELOW - fit.score) / FAIL_BELOW + 0.6),
            thesis_fit=fit.score,
        )
    elif not signals:
        result = ScreeningResult(
            "review",
            "Insufficient data for a first-pass decision — routed to review.",
            confidence=0.4,
            thesis_fit=fit.score,
        )
    elif fit.score < REVIEW_BELOW:
        result = ScreeningResult(
            "review",
            f"Marginal thesis fit ({fit.score}/100) — human review before full scoring.",
            confidence=0.5,
            thesis_fit=fit.score,
        )
    else:
        result = ScreeningResult(
            "pass",
            f"Clears first pass (thesis fit {fit.score}/100, {len(signals)} signals).",
            confidence=min(1.0, fit.score / 100 + 0.3),
            thesis_fit=fit.score,
        )

    repo.set_screening(application_id, result.decision, result.reason)
    db.commit()
    return result
