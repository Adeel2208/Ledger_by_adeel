"""Trend computation (E2): direction from >= 2 historical score points per axis."""
from __future__ import annotations

from app.intelligence.scoring.base import Trend

_EPS = 2.0  # points of change below which we call it stable (noise band)


def compute_trend(history: list[float]) -> Trend:
    """Direction of the most recent move. `history` is oldest -> newest.

    With < 2 points there's no momentum to report yet, so we return STABLE.
    """
    if len(history) < 2:
        return Trend.STABLE
    delta = history[-1] - history[-2]
    if delta > _EPS:
        return Trend.IMPROVING
    if delta < -_EPS:
        return Trend.DECLINING
    return Trend.STABLE
