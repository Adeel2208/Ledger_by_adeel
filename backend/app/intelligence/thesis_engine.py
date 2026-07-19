"""Thesis Engine (FR-1, Epic A).

Runtime-configurable thesis (sectors, stage, geography, check size, ownership,
risk appetite). Produces a 0-100 thesis-fit score. Applied IDENTICALLY to inbound
and outbound founders (A2) — no channel special-casing.

Deterministic and explainable on purpose (NFR: Transparency): fit is a weighted
sum of dimension matches, and every point is attributable to a reason. This is a
RANKING/FILTER score, orthogonal to the three screening axes — it is never merged
into them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.thesis import Thesis

# Weights sum to 1.0. Sector/stage carry most signal for early-stage fit.
_WEIGHTS = {"sector": 0.45, "stage": 0.30, "geography": 0.25}


@dataclass
class ThesisFit:
    score: int                         # 0-100
    reasons: list[str] = field(default_factory=list)
    thesis_id: int | None = None


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _matches(value: str | None, allowed: list[str]) -> bool:
    v = _norm(value)
    if not v or not allowed:
        return False
    # Substring both ways so "Berlin" matches thesis "Europe/Germany" configs loosely,
    # and "AI" matches "AI Infrastructure".
    return any(v in _norm(a) or _norm(a) in v for a in allowed)


def get_active_thesis(db: Session) -> Thesis | None:
    return db.scalars(
        select(Thesis).where(Thesis.is_active.is_(True)).order_by(Thesis.created_at.desc())
    ).first()


def score_company(company: Company, thesis: Thesis) -> ThesisFit:
    """Score one company against a thesis. Returns fit + human-readable reasons.

    Fit is the matched share of the dimensions the thesis actually CONSTRAINS,
    renormalized over those dimensions. An unconstrained dimension is ignored (it
    adds no fit) so a wrong-sector company can't be floated over the bar by the
    thesis simply leaving geography open.
    """
    reasons: list[str] = []
    matched = 0.0
    constrained = 0.0

    checks = {
        "sector": (company.sector, thesis.sectors),
        "stage": (company.stage, thesis.stages),
        "geography": (company.geography, thesis.geographies),
    }
    for dim, (value, allowed) in checks.items():
        if not allowed:
            reasons.append(f"{dim}: unconstrained by thesis")
            continue
        constrained += _WEIGHTS[dim]
        if _matches(value, allowed):
            matched += _WEIGHTS[dim]
            reasons.append(f"{dim}: '{value}' matches thesis")
        else:
            reasons.append(f"{dim}: '{value or 'unknown'}' outside thesis {allowed}")

    if constrained == 0:
        return ThesisFit(score=50, reasons=["thesis constrains nothing — neutral fit"], thesis_id=thesis.id)
    return ThesisFit(score=round(matched / constrained * 100), reasons=reasons, thesis_id=thesis.id)


def score_thesis_fit(company: Company, db: Session) -> ThesisFit:
    """Convenience: score a company against the currently active thesis."""
    thesis = get_active_thesis(db)
    if thesis is None:
        return ThesisFit(score=50, reasons=["no active thesis configured — neutral fit"])
    return score_company(company, thesis)
