"""Entity resolution / deduplication (FR-2, B2) — explainable & auditable.

Production ER pipeline (per the standard blocking->comparison->matching flow):

  1. BLOCKING   — cheaply select candidate founders via deterministic keys
                  (email, github handle) + a name-token block, so we never do an
                  O(n^2) scan across the whole table.
  2. COMPARISON — field-level similarity: exact for strong identifiers, Jaro-Winkler
                  / token-sort for names.
  3. MATCHING   — combine into a score and map to one of three actions using a
                  confidence band:
                      score >= MATCH_THRESHOLD   -> MERGE  (same person)
                      REVIEW_THRESHOLD..MATCH    -> REVIEW (human decides)
                      below REVIEW_THRESHOLD      -> NEW    (distinct person)

Every decision carries `reasons` (which fields drove it) so merges are auditable.
Merging preserves provenance — it never deletes source signals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz.distance import JaroWinkler
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.founder import Founder

MATCH_THRESHOLD = 0.90
REVIEW_THRESHOLD = 0.72


class Action(str, Enum):
    MERGE = "merge"
    REVIEW = "review"
    NEW = "new"


@dataclass
class MatchDecision:
    action: Action
    founder_id: int | None = None
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return JaroWinkler.normalized_similarity(a, b)


def score_pair(identity: dict, founder: Founder) -> MatchDecision:
    """Field-level comparison of an observed identity against one existing founder."""
    reasons: list[str] = []

    # Strong deterministic identifiers -> immediate high-confidence match.
    email = _norm(identity.get("email"))
    if email and email == _norm(founder.email):
        return MatchDecision(Action.MERGE, founder.id, 1.0, ["email exact match"])

    handle = _norm(identity.get("github_handle"))
    if handle and handle == _norm(founder.github_handle):
        return MatchDecision(Action.MERGE, founder.id, 1.0, ["github handle exact match"])

    # Name similarity (probabilistic).
    name_sim = _name_similarity(_norm(identity.get("name")), _norm(founder.name))
    score = name_sim
    if name_sim >= 0.85:
        reasons.append(f"name similarity {name_sim:.2f}")

    # A corroborating soft signal (shared linkedin) nudges an ambiguous name over the line.
    linkedin = _norm(identity.get("linkedin_url"))
    if linkedin and linkedin == _norm(founder.linkedin_url):
        score = min(1.0, score + 0.15)
        reasons.append("linkedin match")

    if score >= MATCH_THRESHOLD:
        action = Action.MERGE
    elif score >= REVIEW_THRESHOLD:
        action = Action.REVIEW
    else:
        action = Action.NEW
    return MatchDecision(action, founder.id, score, reasons)


def _blocking_candidates(identity: dict, db: Session) -> list[Founder]:
    """Cheap pre-filter: only founders sharing an identifier or a name token."""
    email = _norm(identity.get("email"))
    handle = _norm(identity.get("github_handle"))
    name = _norm(identity.get("name"))
    first_token = name.split()[0] if name else None

    clauses = []
    if email:
        clauses.append(Founder.email.ilike(email))
    if handle:
        clauses.append(Founder.github_handle.ilike(handle))
    if first_token:
        clauses.append(Founder.name.ilike(f"%{first_token}%"))

    if not clauses:
        return []
    return list(db.scalars(select(Founder).where(or_(*clauses)).limit(50)))


def resolve(identity: dict, db: Session) -> MatchDecision:
    """Resolve an observed identity to an existing founder, or decide it's new.

    Returns the best decision across all blocking candidates. Callers treat
    MERGE as 'attach to founder_id', REVIEW as 'attach but flag for a human',
    and NEW as 'create a new founder'.
    """
    if not any(identity.get(k) for k in ("name", "email", "github_handle")):
        return MatchDecision(Action.NEW, reasons=["no identifying fields"])

    candidates = _blocking_candidates(identity, db)
    best = MatchDecision(Action.NEW, reasons=["no candidate above threshold"])
    for founder in candidates:
        decision = score_pair(identity, founder)
        if decision.score > best.score:
            best = decision
        if decision.action is Action.MERGE and decision.score >= 1.0:
            break  # deterministic identifier match — cannot be beaten
    return best
