"""Persistent Founder Score engine (FR-7, B3) — a 'credit score for founders'.

Non-negotiable: this score is PERSISTENT. It lives in Memory, follows the founder
across applications/companies, and NEVER resets. It surfaces trend/momentum, not
just the latest snapshot, and is stored versioned for history.

It is ONE INPUT into the Founder screening axis (intelligence/scoring/founder_axis.py),
not a replacement for it.

Design choice: the composition is a TRANSPARENT, DETERMINISTIC heuristic (not a
black-box LLM number) so every point is explainable (NFR: Transparency). Signals
map to five components; each signal's contribution is weighted by its confidence
tier and decayed by age. A single 0-100 composite is produced — this is allowed;
the "never average" rule applies to the three SCREENING axes, not to this score.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models.signal import Signal

# Which components each signal record_type informs, and its base strength (0-1).
# Alternate/cold-start signals (research_paper, public_footprint, product_launch)
# are weighted on par with track-record signals — see docs/COLD_START.md.
_SIGNAL_WEIGHTS: dict[str, dict[str, float]] = {
    "github_profile": {"technical": 0.6, "execution": 0.3},
    "github_repo": {"technical": 0.5, "execution": 0.4},
    "research_paper": {"technical": 0.7, "vision": 0.4},
    "product_launch": {"execution": 0.7, "communication": 0.4},
    "traction_claim": {"execution": 0.5},
    "team_background": {"execution": 0.4, "resilience": 0.3},
    "public_footprint": {"communication": 0.6, "resilience": 0.4},
    "market_size": {"vision": 0.5},
    "problem_statement": {"vision": 0.5, "communication": 0.3},
}

_CONFIDENCE_MULT = {"verified": 1.0, "corroborated": 0.85, "claimed": 0.55, "scraped": 0.4}

COMPONENTS = ("technical", "execution", "communication", "vision", "resilience")
_HALF_LIFE_DAYS = 540.0  # ~18 months; older signals count less but never vanish


def _recency_multiplier(ts: datetime, now: datetime) -> float:
    age_days = max(0.0, (now - _aware(ts)).days)
    return 0.5 ** (age_days / _HALF_LIFE_DAYS)  # exponential decay, in (0, 1]


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _component_scores(signals: list[Signal], now: datetime) -> dict[str, float]:
    # Accumulate weighted evidence per component, then squash to 0-100 so a founder
    # with lots of strong signal saturates rather than growing unbounded.
    raw: dict[str, float] = {c: 0.0 for c in COMPONENTS}
    for sig in signals:
        weights = _SIGNAL_WEIGHTS.get(sig.record_type)
        if not weights:
            continue
        mult = _CONFIDENCE_MULT.get(sig.confidence, 0.5) * _recency_multiplier(
            sig.source_timestamp, now
        )
        for component, base in weights.items():
            raw[component] += base * mult
    # Saturating map: 100 * (1 - e^-x). ~3 units of strong evidence ≈ 95/100.
    return {c: round(100 * (1 - math.exp(-v)), 1) for c, v in raw.items()}


def compute_founder_score(founder_id: int, db: Session) -> dict:
    """Recompute the persistent score from all-time signals; append to history.

    Returns {value, momentum, components, computed_at}. Momentum compares this
    composite to the previous stored score (improving / stable / declining).
    """
    repo = MemoryRepository(db)
    now = datetime.now(timezone.utc)
    signals = repo.signals_for(founder_id)

    components = _component_scores(signals, now)
    # Composite: mean of the components we actually have EVIDENCE for. Absence of a
    # component (e.g. no GitHub for a cold-start founder) is treated as UNKNOWN, not
    # as zero capability — averaging in the zeros would penalize missing traditional
    # signals, the exact anti-pattern docs/COLD_START.md forbids.
    observed = [v for v in components.values() if v > 0]
    value = round(sum(observed) / len(observed), 1) if observed else 0.0

    previous = repo.latest_score(founder_id)
    if previous is None:
        momentum = "stable"
    elif value > previous.value + 2:
        momentum = "improving"
    elif value < previous.value - 2:
        momentum = "declining"
    else:
        momentum = "stable"

    repo.add_founder_score(founder_id, value, momentum, components)
    return {"value": value, "momentum": momentum, "components": components, "computed_at": now}
