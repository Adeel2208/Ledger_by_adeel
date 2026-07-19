"""Sourcing & channel intelligence (stretch I3).

Tracks which sourcing channels historically produce the strongest opportunities,
and surfaces underexplored sources to try next — so sourcing improves over time
rather than staying static. Aggregates only from persisted data (applications,
scores, signals); no new logging needed.
"""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence.thesis_engine import score_thesis_fit
from app.memory.ingestion.registry import available_sources
from app.memory.repository import MemoryRepository
from app.models.signal import Signal


def _avg(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 1) if xs else None


def channel_performance(db: Session) -> dict:
    repo = MemoryRepository(db)
    apps = repo.list_applications()

    # ── Performance by channel (inbound vs outbound) ──────────────────────────
    buckets: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "thesis": [], "founder": [], "passes": 0, "axes": defaultdict(list)}
    )
    for app in apps:
        company = repo.get_company(app.company_id)
        b = buckets[app.channel]
        b["count"] += 1
        b["thesis"].append(score_thesis_fit(company, db).score)
        fs = repo.latest_score(app.founder_id)
        b["founder"].append(fs.value if fs else None)
        if app.screening_decision == "pass":
            b["passes"] += 1
        for axis, row in repo.latest_axis_scores(app.id).items():
            b["axes"][axis].append(row.value)

    by_channel = []
    for channel, b in buckets.items():
        by_channel.append(
            {
                "channel": channel,
                "count": b["count"],
                "avg_thesis_fit": _avg(b["thesis"]),
                "avg_founder_score": _avg(b["founder"]),
                "pass_rate": round(b["passes"] / b["count"], 2) if b["count"] else 0,
                "avg_axes": {a: _avg(v) for a, v in b["axes"].items()},
            }
        )
    by_channel.sort(key=lambda r: (r["avg_founder_score"] or 0), reverse=True)

    # ── Source distribution (which raw sources bring founders) ────────────────
    rows = db.execute(select(Signal.source, Signal.founder_id)).all()
    founders_by_source: dict[str, set] = defaultdict(set)
    for source, founder_id in rows:
        base = source.split(":")[0]  # "deck:slide-4" -> "deck"
        founders_by_source[base].add(founder_id)
    by_source = sorted(
        ({"source": s, "founders": len(f)} for s, f in founders_by_source.items()),
        key=lambda r: r["founders"],
        reverse=True,
    )

    # ── Underexplored channels (registered but low/no yield) ──────────────────
    seen = {r["source"] for r in by_source}
    underexplored = [s for s in available_sources() if s not in seen or founders_by_source[s].__len__() <= 1]

    # A concrete, data-driven suggestion.
    best = by_channel[0]["channel"] if by_channel else None
    suggestion = None
    if underexplored:
        suggestion = (
            f"'{best}' currently yields your strongest founders. "
            f"Underexplored sources worth scanning next: {', '.join(underexplored[:3])}."
        )

    return {
        "by_channel": by_channel,
        "by_source": by_source,
        "underexplored": underexplored,
        "suggestion": suggestion,
    }
