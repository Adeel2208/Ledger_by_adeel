"""Evidence tracing + Trust Score (FR-8, F1, stretch I1).

Links every factual claim to specific Evidence row(s) with a confidence tier
(verified > corroborated > claimed > scraped). A claim with no evidence CANNOT be
marked verified — its confidence is downgraded to reflect that it's unsupported.

The Trust Score rates the *evidence quality* of a memo (not the deal quality):
strong when claims are backed by high-tier sources, dragged down by contradictions
and disclosed gaps.
"""
from __future__ import annotations

from app.schemas.common import Confidence
from app.schemas.memo import Contradiction

# Confidence tier -> quality weight for the trust score.
_TIER_WEIGHT = {"verified": 1.0, "corroborated": 0.8, "claimed": 0.5, "scraped": 0.35}
_NO_EVIDENCE_WEIGHT = 0.2
_SEVERITY_PENALTY = {"low": 0.04, "medium": 0.08, "high": 0.12}
_GAP_PENALTY = 0.03


def reconcile_claim_confidence(stated: Confidence, evidence_tiers: list[str]) -> Confidence:
    """A claim can't outrank its evidence. With no evidence it can't be 'verified'.

    Returns the lower of the stated confidence and the best evidence tier — so an
    LLM that over-claims 'verified' without citing a verified source gets corrected.
    """
    if not evidence_tiers:
        # Unsupported claim: cap at 'claimed' at best (never verified/corroborated).
        return Confidence.CLAIMED if stated.rank >= Confidence.CLAIMED.rank else stated
    best_evidence = max((Confidence(t) for t in evidence_tiers), key=lambda c: c.rank)
    return stated if stated.rank <= best_evidence.rank else best_evidence


def compute_trust_score(
    claim_confidences: list[str], contradictions: list[Contradiction], gap_count: int
) -> float:
    """0-100 evidence-quality score for the whole memo."""
    if not claim_confidences:
        base = _NO_EVIDENCE_WEIGHT
    else:
        base = sum(_TIER_WEIGHT.get(c, _NO_EVIDENCE_WEIGHT) for c in claim_confidences) / len(
            claim_confidences
        )
    penalty = sum(_SEVERITY_PENALTY.get(c.severity, 0.08) for c in contradictions)
    penalty += min(gap_count * _GAP_PENALTY, 0.15)  # gaps hurt, but honesty is capped-penalty
    return round(max(0.0, min(1.0, base - penalty)) * 100, 1)
