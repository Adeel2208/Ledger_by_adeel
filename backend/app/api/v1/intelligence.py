"""Advanced intelligence and analytics endpoints.

Exposes signal analysis, predictive analytics, and deep insights.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence.anomaly_detector import AnomalyDetector
from app.intelligence.pattern_miner import PatternMiningEngine
from app.intelligence.predictive import PredictiveEngine
from app.intelligence.signal_analyzer import SignalCorrelationEngine

router = APIRouter()


class FounderAnalysisRequest(BaseModel):
    founder_id: int


class TrajectoryRequest(BaseModel):
    founder_id: int
    horizon_months: int = Field(default=12, ge=1, le=36, description="Forecast horizon (1-36 months)")


@router.post("/analyze")
def analyze_founder_signals(req: FounderAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """
    Comprehensive signal correlation analysis for a founder.
    
    Returns:
    - Consistency score (data quality)
    - Detected contradictions across sources
    - Momentum indicators (accelerating/declining)
    - Quality signals
    - Network effects
    - Red flags and green flags
    """
    engine = SignalCorrelationEngine(db)
    
    try:
        report = engine.analyze_founder_signals(req.founder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    return {
        "founder_id": report.founder_id,
        "consistency_score": report.consistency_score,
        "confidence": report.confidence,
        "analyzed_signal_count": report.analyzed_signal_count,
        "contradictions": [
            {
                "metric": c.metric,
                "severity": c.severity,
                "explanation": c.explanation,
                "sources": c.sources,
                "values": c.values,
            }
            for c in report.contradictions
        ],
        "momentum_indicators": [
            {
                "dimension": m.dimension,
                "direction": m.direction,
                "velocity": m.velocity,
                "timespan_days": m.timespan_days,
                "confidence": m.confidence,
            }
            for m in report.momentum_indicators
        ],
        "quality_signals": [
            {
                "indicator": q.indicator,
                "score": q.score,
                "evidence": q.evidence,
                "weight": q.weight,
            }
            for q in report.quality_signals
        ],
        "network_effects": [
            {
                "effect_type": n.effect_type,
                "strength": n.strength,
                "evidence": n.evidence,
            }
            for n in report.network_effects
        ],
        "red_flags": report.red_flags,
        "green_flags": report.green_flags,
        "generated_at": report.generated_at.isoformat(),
    }


@router.post("/forecast")
def forecast_trajectory(req: TrajectoryRequest, db: Session = Depends(get_db)) -> dict:
    """
    Predict future trajectory for key metrics.
    
    Returns forecasts for:
    - Revenue (ARR)
    - User growth
    - Team size
    
    Plus identified inflection points and confidence intervals.
    """
    engine = PredictiveEngine(db)
    
    try:
        forecast = engine.forecast_trajectory(req.founder_id, req.horizon_months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")
    
    return {
        "founder_id": forecast.founder_id,
        "horizon_months": forecast.horizon_months,
        "confidence": forecast.confidence,
        "model_used": forecast.model_used,
        "revenue_forecast": forecast.revenue_forecast,
        "user_growth_forecast": forecast.user_growth_forecast,
        "team_size_forecast": forecast.team_size_forecast,
        "inflection_points": forecast.inflection_points,
        "generated_at": forecast.generated_at.isoformat(),
    }


@router.post("/success-probability")
def calculate_success_probability(req: FounderAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """
    Calculate probability of reaching key milestones.
    
    Returns probabilities for:
    - Product-market fit
    - Series A funding
    - Profitability
    - Exit potential
    
    Plus key drivers, risk factors, and timing estimates.
    """
    engine = PredictiveEngine(db)
    
    try:
        prob = engine.calculate_success_probability(req.founder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Probability calculation failed: {str(e)}")
    
    return {
        "founder_id": prob.founder_id,
        "confidence": prob.confidence,
        "probabilities": {
            "product_market_fit": prob.product_market_fit_prob,
            "series_a_funding": prob.series_a_funding_prob,
            "profitability": prob.profitability_prob,
            "exit_potential": prob.exit_potential_prob,
        },
        "key_drivers": prob.key_drivers,
        "risk_factors": prob.risk_factors,
        "timing_estimates": {
            "months_to_pmf": prob.expected_months_to_pmf,
            "months_to_funding": prob.expected_months_to_funding,
        },
        "generated_at": prob.generated_at.isoformat(),
    }


@router.post("/risk-assessment")
def assess_risk(req: FounderAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """
    Comprehensive risk assessment across multiple dimensions.
    
    Returns:
    - Execution risk
    - Market timing risk
    - Team risk
    - Competitive risk
    - Financial risk
    - Overall risk score and level
    - Detailed risk factors
    - Mitigation suggestions
    """
    engine = PredictiveEngine(db)
    
    try:
        risk = engine.assess_risk(req.founder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")
    
    return {
        "founder_id": risk.founder_id,
        "overall_risk": risk.overall_risk,
        "risk_level": risk.risk_level,
        "risk_dimensions": {
            "execution": risk.execution_risk,
            "market_timing": risk.market_timing_risk,
            "team": risk.team_risk,
            "competitive": risk.competitive_risk,
            "financial": risk.financial_risk,
        },
        "risk_factors": risk.risk_factors,
        "mitigation_suggestions": risk.mitigation_suggestions,
        "generated_at": risk.generated_at.isoformat(),
    }


@router.post("/optimal-timing")
def determine_optimal_timing(req: FounderAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """
    Determine optimal investment timing based on trajectory and risk.
    
    Returns:
    - Recommendation (invest_now, wait_X_months, pass)
    - Reasoning
    - Expected milestones if waiting
    - Opportunity window
    - Urgency score
    """
    engine = PredictiveEngine(db)
    
    try:
        timing = engine.determine_optimal_timing(req.founder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timing analysis failed: {str(e)}")
    
    return {
        "founder_id": timing.founder_id,
        "recommendation": timing.recommendation,
        "reasoning": timing.reasoning,
        "wait_months": timing.wait_months,
        "expected_milestones": timing.expected_milestones,
        "window_closing_in_months": timing.window_closing_in_months,
        "urgency_score": timing.urgency_score,
        "generated_at": timing.generated_at.isoformat(),
    }


class PatternMiningRequest(BaseModel):
    lookback_months: int = Field(default=24, ge=1, le=60, description="Historical data to analyze (1-60 months)")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence for patterns")


@router.post("/mine-patterns")
def mine_success_patterns(req: PatternMiningRequest, db: Session = Depends(get_db)) -> dict:
    """
    Mine success patterns from historical decisions.
    
    Analyzes past applications to identify:
    - High-confidence success patterns
    - Common failure modes
    - Key success factors
    - Thesis optimization recommendations
    
    Use this to learn from history and improve investment strategy.
    """
    engine = PatternMiningEngine(db)
    
    try:
        patterns = engine.mine_success_patterns(
            lookback_months=req.lookback_months,
            min_confidence=req.min_confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern mining failed: {str(e)}")
    
    return {
        "analyzed_applications": patterns.analyzed_applications,
        "success_patterns": [
            {
                "pattern": p.pattern_name,
                "confidence": p.confidence,
                "support": p.support,
                "attributes": p.attributes,
                "example_founders": p.examples,
            }
            for p in patterns.high_confidence_rules
        ],
        "failure_modes": [
            {
                "mode": f.mode_name,
                "frequency": f.frequency,
                "indicators": f.indicators,
                "example_founders": f.examples,
            }
            for f in patterns.failure_modes
        ],
        "key_success_factors": [
            {"factor": factor, "importance": importance}
            for factor, importance in patterns.key_success_factors
        ],
        "thesis_optimization": {
            "current_performance": patterns.thesis_optimization.current_performance,
            "recommended_changes": patterns.thesis_optimization.recommended_changes,
            "expected_improvement": patterns.thesis_optimization.expected_improvement,
            "reasoning": patterns.thesis_optimization.reasoning,
        },
        "generated_at": patterns.generated_at.isoformat(),
    }


@router.post("/anomaly-detection")
def detect_anomalies(req: FounderAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """
    Detect anomalies and red flags in founder data.
    
    Returns:
    - Statistical anomalies (unusual metrics)
    - Behavioral anomalies (suspicious patterns)
    - Temporal anomalies (retroactive changes, gaps)
    - Network anomalies (isolation, fake engagement)
    - Overall risk level
    - Recommended action
    """
    detector = AnomalyDetector(db)
    
    try:
        report = detector.detect_anomalies(req.founder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")
    
    return {
        "founder_id": report.founder_id,
        "overall_risk_level": report.overall_risk_level,
        "recommended_action": report.recommended_action,
        "anomaly_count": report.anomaly_count,
        "statistical_anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "evidence": a.evidence,
                "confidence": a.confidence,
            }
            for a in report.statistical_anomalies
        ],
        "behavioral_anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "evidence": a.evidence,
                "confidence": a.confidence,
            }
            for a in report.behavioral_anomalies
        ],
        "temporal_anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "evidence": a.evidence,
                "confidence": a.confidence,
            }
            for a in report.temporal_anomalies
        ],
        "network_anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "evidence": a.evidence,
                "confidence": a.confidence,
            }
            for a in report.network_anomalies
        ],
        "generated_at": report.generated_at.isoformat(),
    }


@router.post("/complete-intelligence")
def complete_intelligence_report(req: FounderAnalysisRequest, db: Session = Depends(get_db)) -> dict:
    """
    Complete intelligence package - all analytics in one call.
    
    Combines:
    - Signal correlation analysis
    - Trajectory forecast
    - Success probability
    - Risk assessment
    - Optimal timing
    
    Use this for a comprehensive founder evaluation.
    """
    signal_engine = SignalCorrelationEngine(db)
    pred_engine = PredictiveEngine(db)
    detector = AnomalyDetector(db)
    
    try:
        # Run all analyses
        signal_analysis = signal_engine.analyze_founder_signals(req.founder_id)
        forecast = pred_engine.forecast_trajectory(req.founder_id, horizon_months=12)
        success_prob = pred_engine.calculate_success_probability(req.founder_id)
        risk = pred_engine.assess_risk(req.founder_id)
        timing = pred_engine.determine_optimal_timing(req.founder_id)
        anomalies = detector.detect_anomalies(req.founder_id)
        
        return {
            "founder_id": req.founder_id,
            "signal_analysis": {
                "consistency_score": signal_analysis.consistency_score,
                "confidence": signal_analysis.confidence,
                "red_flags": signal_analysis.red_flags,
                "green_flags": signal_analysis.green_flags,
                "contradictions_count": len(signal_analysis.contradictions),
                "momentum_indicators_count": len(signal_analysis.momentum_indicators),
            },
            "forecast": {
                "horizon_months": forecast.horizon_months,
                "revenue_forecast": forecast.revenue_forecast,
                "confidence": forecast.confidence,
                "inflection_points": forecast.inflection_points,
            },
            "success_probability": {
                "product_market_fit": success_prob.product_market_fit_prob,
                "series_a_funding": success_prob.series_a_funding_prob,
                "key_drivers": success_prob.key_drivers,
                "risk_factors": success_prob.risk_factors,
            },
            "risk_assessment": {
                "overall_risk": risk.overall_risk,
                "risk_level": risk.risk_level,
                "risk_factors": risk.risk_factors,
            },
            "optimal_timing": {
                "recommendation": timing.recommendation,
                "reasoning": timing.reasoning,
                "urgency_score": timing.urgency_score,
            },
            "anomaly_detection": {
                "overall_risk_level": anomalies.overall_risk_level,
                "recommended_action": anomalies.recommended_action,
                "anomaly_count": anomalies.anomaly_count,
                "critical_flags": [
                    a.description for a in (
                        anomalies.statistical_anomalies +
                        anomalies.behavioral_anomalies +
                        anomalies.temporal_anomalies +
                        anomalies.network_anomalies
                    ) if a.severity in ("critical", "high")
                ][:5],  # Top 5 critical flags
            },
            "generated_at": signal_analysis.generated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete intelligence report failed: {str(e)}")
