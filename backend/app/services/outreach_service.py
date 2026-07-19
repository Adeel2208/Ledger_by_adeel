"""Outreach service — drafts the cold-outreach message that triggers activation.

The brief's outbound loop is "cold outreach, not cold investment": the goal of
contacting a discovered founder is a real application, not a blind term sheet.
The draft is grounded in the founder's *own observed signals* — the message
demonstrates that the fund noticed their actual work, which is the entire
equity story ("not because of who they know, but what the system knows about
them"). Nothing is invented: the prompt receives only stored signals, and a
failed draft degrades to None rather than blocking activation.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.llm.client import get_llm
from app.memory.repository import MemoryRepository

logger = logging.getLogger(__name__)

_SYSTEM = """You draft short cold-outreach messages from a venture fund to a founder
the fund discovered through public signals. Rules:
- 90-130 words, warm but specific; no hype, no flattery inflation.
- Reference ONLY the observations provided — never invent achievements.
- Name 1-2 concrete things the fund noticed (a repo, a paper, traction).
- The ask: invite them to apply (deck + company name, decision within 24 hours).
- Sign off as "The VC Brain team". Output the message body only."""

_MAX_OBSERVATIONS = 8  # enough grounding without blowing the prompt


def draft_outreach(founder_id: int, db: Session) -> str | None:
    """Draft a personalised outreach message, or None if it can't be grounded.

    A founder with no signals gets no draft — an ungrounded message would be
    generic spam and would undercut the "we noticed your work" premise.
    """
    repo = MemoryRepository(db)
    founder = repo.get_founder(founder_id)
    if founder is None:
        return None

    signals = repo.signals_for(founder_id)
    if not signals:
        return None

    observations = []
    for s in signals[:_MAX_OBSERVATIONS]:
        text = (s.payload or {}).get("text") or (s.payload or {}).get("description") or ""
        observations.append(f"- [{s.source}/{s.record_type}] {str(text)[:200]}")

    prompt = (
        f"Founder: {founder.name}\n"
        f"GitHub: {founder.github_handle or 'unknown'}\n"
        f"Observed signals:\n" + "\n".join(observations)
    )

    try:
        return get_llm().complete(prompt, system=_SYSTEM, temperature=0.4, fast=True).strip()
    except Exception as exc:  # outreach must never block activation
        logger.warning("Outreach draft failed for founder %s: %s", founder_id, exc)
        return None
