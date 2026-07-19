"""Absence of evidence must never read as evidence of badness.

A founder with no ingested signals is *undetermined*, not risky, not failing,
and not flagged. These tests lock that in across all three engines, because the
natural default in each of them was to emit a maximally-negative empty report —
which would penalise exactly the cold-start founders the product exists to find.
"""
from __future__ import annotations

from app.intelligence.anomaly_detector import AnomalyDetector
from app.intelligence.predictive import PredictiveEngine
from app.intelligence.signal_analyzer import SignalCorrelationEngine


def _founder_with_no_signals(db) -> int:
    """Create a founder that has no signals attached."""
    from app.models.founder import Founder

    f = Founder(name="Signalless Founder", is_cold_start=True)
    db.add(f)
    db.commit()
    return f.id


def test_risk_is_unknown_not_critical(db_session):
    """No signals -> risk undetermined, never 'critical'."""
    fid = _founder_with_no_signals(db_session)
    risk = PredictiveEngine(db_session).assess_risk(fid)

    assert risk.risk_level == "unknown"
    assert risk.overall_risk == 0.0
    # Every dimension must be undetermined too, not maxed out.
    assert risk.execution_risk == 0.0
    assert risk.team_risk == 0.0


def test_timing_is_insufficient_data_not_pass(db_session):
    """No signals -> 'insufficient_data', never a 'pass' verdict.

    Also guards the opposite failure: undetermined risk must not fall through
    to 'invest_now' on zero evidence.
    """
    fid = _founder_with_no_signals(db_session)
    timing = PredictiveEngine(db_session).determine_optimal_timing(fid)

    assert timing.recommendation == "insufficient_data"
    assert timing.recommendation != "invest_now"
    assert timing.urgency_score == 0.0


def test_no_signals_raises_no_red_flags(db_session):
    """Having no paper trail is a coverage gap, not a red flag."""
    fid = _founder_with_no_signals(db_session)
    report = SignalCorrelationEngine(db_session).analyze_founder_signals(fid)

    assert report.red_flags == []
    assert report.analyzed_signal_count == 0


def test_empty_anomaly_report_does_not_demand_investigation(db_session):
    """Nothing examined means nothing to investigate."""
    fid = _founder_with_no_signals(db_session)
    report = AnomalyDetector(db_session).detect_anomalies(fid)

    assert report.anomaly_count == 0
    assert report.recommended_action == "gather_data"
