"""Enrichment, freshness & coverage (FR-2, B1).

Two jobs:
  1. FRESHNESS — per-source recency + overall reliability mix, so the UI can show
     a data-freshness indicator and stale data can be refreshed.
  2. COVERAGE / GAPS — an explicit inventory of which expected data is present vs
     genuinely missing. This is what powers honest gap-flagging in memos (F3):
     a missing field becomes a disclosed gap, never a fabricated value.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository

# Data facets we hope to have on a founder/opportunity, and the signal record_types
# that satisfy each. Absence => an explicit gap (disclosed, never invented).
_EXPECTED_FACETS: dict[str, set[str]] = {
    "technical_footprint": {"github_profile", "github_repo", "research_paper"},
    "traction": {"traction_claim", "product_launch"},
    "team": {"team_background"},
    "market": {"market_size", "problem_statement"},
    "public_presence": {"public_footprint"},
}


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def assess(founder_id: int, db: Session) -> dict:
    """Return freshness + coverage report for a founder's data."""
    repo = MemoryRepository(db)
    signals = repo.signals_for(founder_id)
    now = datetime.now(timezone.utc)

    present_types = {s.record_type for s in signals}

    # Freshness per source.
    by_source: dict[str, datetime] = {}
    reliability: dict[str, int] = {}
    for s in signals:
        ts = _aware(s.source_timestamp)
        if s.source not in by_source or ts > by_source[s.source]:
            by_source[s.source] = ts
        reliability[s.confidence] = reliability.get(s.confidence, 0) + 1

    freshness = {
        source: {"last_seen": ts.isoformat(), "age_days": (now - ts).days}
        for source, ts in by_source.items()
    }

    # Coverage / gaps.
    covered, gaps = [], []
    for facet, types in _EXPECTED_FACETS.items():
        (covered if present_types & types else gaps).append(facet)

    return {
        "signal_count": len(signals),
        "freshness": freshness,
        "reliability_mix": reliability,
        "covered": covered,
        "gaps": gaps,  # explicit missing facets -> disclosed, never fabricated
    }
