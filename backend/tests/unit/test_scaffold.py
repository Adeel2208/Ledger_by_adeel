"""Guardrail tests that encode the non-negotiables (Requirements section 12).

These are cheap tripwires: if a future change violates a hard rule, a test fails.
"""
from __future__ import annotations

from app.intelligence.scoring.base import TripleScore


def test_triple_score_has_no_composite_accessor():
    """The three axes must never be collapsible into one number (FR-6)."""
    assert not hasattr(TripleScore, "overall")
    assert not hasattr(TripleScore, "average")
    assert not hasattr(TripleScore, "composite")


def test_models_import_and_register():
    """Every table wires onto Base.metadata (data foundation, 30% weight)."""
    from app.database import Base

    expected = {
        "founders",
        "companies",
        "applications",
        "signals",
        "axis_scores",
        "founder_scores",
        "memos",
        "evidence",
        "theses",
        "outreach",
    }
    assert expected <= set(Base.metadata.tables)
