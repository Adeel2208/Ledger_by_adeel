"""Contradiction detection (FR-8, F2).

Cross-reference a founder's signals and flag conflicts (e.g. a claimed traction
metric that conflicts with an independent source) BEFORE they reach the investor.
Flag, never silently resolve.

LLM-backed but structured: returns pairs of conflicting signal IDs with a severity,
so the memo can mark the affected claims `contradicted=True` and the investor can
inspect both sides.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.scoring.base import signal_context
from app.memory.repository import MemoryRepository
from app.schemas.memo import Contradiction, Contradictions

_SYSTEM = (
    "You are a diligence fact-checker. Given a founder's evidence signals, identify "
    "pairs that CONTRADICT each other — e.g. a self-reported metric that conflicts with "
    "an independent source, or inconsistent figures. Only report genuine conflicts; if "
    "there are none, return an empty list. Reference signals by their numeric IDs."
)


def detect_contradictions(application_id: int, db: Session, llm=None) -> list[Contradiction]:
    repo = MemoryRepository(db)
    app = repo.get_application(application_id)
    signals = repo.signals_for(app.founder_id)
    if len(signals) < 2:
        return []

    if llm is None:
        from app.llm.client import get_llm

        llm = get_llm()

    prompt = (
        f"Signals:\n{signal_context(signals)}\n\n"
        "List any contradictions between these signals as pairs of signal IDs."
    )
    valid = {s.id for s in signals}
    result: Contradictions = llm.structured(prompt, Contradictions, system=_SYSTEM)
    # Drop any hallucinated signal IDs.
    return [
        c for c in result.contradictions if c.signal_id_a in valid and c.signal_id_b in valid
    ]
