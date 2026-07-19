"""Predictive analytics engine for trajectory forecasting and success probability.

Uses historical signal patterns to predict future outcomes, optimal timing,
and risk assessment. This is forward-looking intelligence, not just historical reporting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models.application import Application
from app.models.founder import Founder
from app.models.signal import Signal


@dataclass
class TrajectoryForecast:
    """Predicted trajectory for key metrics."""
    founder_id: int
    horizon_months: int
    
    # Predictions with confidence intervals
    revenue_forecast: dict[str, Any]  # {predicted, lower_bound, upper_bound, monthly}
    user_growth_forecast: dict[str, Any]
    team_size_forecast: dict[str, Any]
    
    # Identified inflection points
    inflection_points: list[dict[str, Any]]
    
    # Model confidence
    confidence: float
    model_used: str
    generated_at: datetime


@dataclass
class SuccessProbability:
    """Probability of reaching various milestones."""
    founder_id: int
    
    # Milestone probabilities (0-1)
    product_market_fit_prob: float
    series_a_funding_prob: float
    profitability_prob: float
    exit_potential_prob: float
    
    # Contributing factors
    key_drivers: list[str]
    risk_factors: list[str]
    
    # Timing estimates
    expected_months_to_pmf: int | None
    expected_months_to_funding: int | None
    
    confidence: float
    generated_at: datetime


@dataclass
class RiskAssessment:
    """Comprehensive risk scoring."""
    founder_id: int
    
    # Risk categories (0-1, higher = more risk)
    execution_risk: float
    market_timing_risk: float
    team_risk: float
    competitive_risk: float
    financial_risk: float
    
    # Overall risk score
    overall_risk: float
    risk_level: str  # low, medium, high, critical
    
    # Detailed breakdown
    risk_factors: list[dict[str, Any]]
    mitigation_suggestions: list[str]
    
    generated_at: datetime


@dataclass
class OptimalTiming:
    """Optimal timing recommendation."""
    founder_id: int
    
    recommendation: str  # invest_now, wait_X_months, pass
    reasoning: list[str]
    
    # If wait recommendation
    wait_months: int | None
    expected_milestones: list[str]
    
    # Opportunity window
    window_closing_in_months: int | None
    urgency_score: float  # 0-1
    
    generated_at: datetime


class PredictiveEngine:
    """Predictive analytics for founders."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)
    
    def forecast_trajectory(
        self, 
        founder_id: int, 
        horizon_months: int = 12
    ) -> TrajectoryForecast:
        """Forecast future trajectory for key metrics."""
        signals = self.repo.signals_for(founder_id)
        
        if not signals:
            return self._empty_forecast(founder_id, horizon_months)
        
        # Extract historical time series
        history = self._build_historical_series(signals)
        
        # Forecast each dimension
        revenue_forecast = self._forecast_revenue(history, horizon_months)
        user_forecast = self._forecast_users(history, horizon_months)
        team_forecast = self._forecast_team_size(history, horizon_months)
        
        # Identify inflection points
        inflections = self._detect_inflection_points(
            revenue_forecast, user_forecast, team_forecast
        )
        
        # Calculate confidence based on data quality
        confidence = self._calculate_forecast_confidence(history, horizon_months)
        
        return TrajectoryForecast(
            founder_id=founder_id,
            horizon_months=horizon_months,
            revenue_forecast=revenue_forecast,
            user_growth_forecast=user_forecast,
            team_size_forecast=team_forecast,
            inflection_points=inflections,
            confidence=confidence,
            model_used="exponential_smoothing",
            generated_at=datetime.now(timezone.utc),
        )
    
    def calculate_success_probability(
        self, founder_id: int
    ) -> SuccessProbability:
        """Calculate probability of reaching key milestones."""
        signals = self.repo.signals_for(founder_id)
        founder = self.repo.get_founder(founder_id)
        
        if not signals or not founder:
            return self._empty_success_prob(founder_id)
        
        # Extract features
        features = self._extract_success_features(founder_id, signals)
        
        # Calculate probabilities using heuristic model
        # (In production, this would be a trained ML model)
        pmf_prob = self._estimate_pmf_probability(features)
        funding_prob = self._estimate_funding_probability(features)
        profit_prob = self._estimate_profitability_probability(features)
        exit_prob = self._estimate_exit_probability(features)
        
        # Identify key drivers
        drivers = self._identify_key_drivers(features)
        risks = self._identify_risk_factors(features)
        
        # Estimate timing
        months_to_pmf = self._estimate_time_to_pmf(features)
        months_to_funding = self._estimate_time_to_funding(features)
        
        # Overall confidence based on signal quality
        confidence = self._calculate_probability_confidence(signals)
        
        return SuccessProbability(
            founder_id=founder_id,
            product_market_fit_prob=pmf_prob,
            series_a_funding_prob=funding_prob,
            profitability_prob=profit_prob,
            exit_potential_prob=exit_prob,
            key_drivers=drivers,
            risk_factors=risks,
            expected_months_to_pmf=months_to_pmf,
            expected_months_to_funding=months_to_funding,
            confidence=confidence,
            generated_at=datetime.now(timezone.utc),
        )
    
    def assess_risk(self, founder_id: int) -> RiskAssessment:
        """Comprehensive risk assessment."""
        signals = self.repo.signals_for(founder_id)
        founder = self.repo.get_founder(founder_id)
        
        if not signals:
            return self._empty_risk_assessment(founder_id)
        
        # Calculate risk across dimensions
        execution_risk = self._assess_execution_risk(signals, founder)
        market_risk = self._assess_market_timing_risk(signals)
        team_risk = self._assess_team_risk(signals, founder)
        competitive_risk = self._assess_competitive_risk(signals)
        financial_risk = self._assess_financial_risk(signals)
        
        # Overall risk (weighted average)
        overall = (
            execution_risk * 0.3 +
            market_risk * 0.25 +
            team_risk * 0.2 +
            competitive_risk * 0.15 +
            financial_risk * 0.1
        )
        
        # Risk level
        if overall < 0.3:
            level = "low"
        elif overall < 0.5:
            level = "medium"
        elif overall < 0.7:
            level = "high"
        else:
            level = "critical"
        
        # Detailed factors
        risk_factors = self._compile_risk_factors(
            execution_risk, market_risk, team_risk, 
            competitive_risk, financial_risk, signals
        )
        
        # Mitigation suggestions
        mitigations = self._suggest_mitigations(risk_factors)
        
        return RiskAssessment(
            founder_id=founder_id,
            execution_risk=execution_risk,
            market_timing_risk=market_risk,
            team_risk=team_risk,
            competitive_risk=competitive_risk,
            financial_risk=financial_risk,
            overall_risk=overall,
            risk_level=level,
            risk_factors=risk_factors,
            mitigation_suggestions=mitigations,
            generated_at=datetime.now(timezone.utc),
        )
    
    def determine_optimal_timing(
        self, founder_id: int
    ) -> OptimalTiming:
        """Determine optimal investment timing."""
        # Get trajectory and success probability
        trajectory = self.forecast_trajectory(founder_id, horizon_months=12)
        success_prob = self.calculate_success_probability(founder_id)
        risk = self.assess_risk(founder_id)
        
        # Decision logic.
        # Insufficient evidence is checked FIRST and on its own: with no signals
        # the probabilities are 0.0 and risk is "unknown" (0.0), which would
        # otherwise fall through to "pass" (penalising a founder for having no
        # paper trail) or, once risk reads 0.0, to "invest_now" on zero
        # evidence. Neither is a real finding — say so explicitly instead.
        if risk.risk_level == "unknown" or success_prob.confidence == 0.0:
            recommendation = "insufficient_data"
            reasoning = [
                "Not enough signals to time this investment.",
                "This is a data gap, not a negative signal about the founder.",
                "Ingest a deck, GitHub, or web signals to enable a recommendation.",
            ]
            wait_months = None
            urgency = 0.0
            window_closing = None

        elif success_prob.product_market_fit_prob > 0.7 and risk.overall_risk < 0.4:
            recommendation = "invest_now"
            reasoning = [
                f"High PMF probability ({success_prob.product_market_fit_prob:.0%})",
                f"Low risk level ({risk.risk_level})",
                "Strong momentum indicators"
            ]
            wait_months = None
            urgency = 0.8
            window_closing = 3  # Competitive pressure
        
        elif success_prob.product_market_fit_prob > 0.5 and risk.overall_risk < 0.6:
            # Wait for better signal
            wait_months = success_prob.expected_months_to_pmf or 6
            recommendation = f"wait_{wait_months}_months"
            reasoning = [
                f"Moderate PMF probability ({success_prob.product_market_fit_prob:.0%})",
                f"Wait for {wait_months} months to see key milestones",
                "Risk manageable but not optimal yet"
            ]
            urgency = 0.4
            window_closing = 12
        
        else:
            # Pass or very long wait
            recommendation = "pass"
            reasoning = [
                f"Low success probability ({success_prob.product_market_fit_prob:.0%})",
                f"High risk level ({risk.risk_level})",
                "Does not meet investment criteria"
            ]
            wait_months = None
            urgency = 0.1
            window_closing = None
        
        # Expected milestones
        expected = []
        if wait_months:
            if trajectory.revenue_forecast.get("predicted"):
                expected.append(
                    f"Revenue: ${trajectory.revenue_forecast['predicted'][-1]:,.0f} ARR"
                )
            if trajectory.user_growth_forecast.get("predicted"):
                expected.append(
                    f"Users: {trajectory.user_growth_forecast['predicted'][-1]:,.0f}"
                )
        
        return OptimalTiming(
            founder_id=founder_id,
            recommendation=recommendation,
            reasoning=reasoning,
            wait_months=wait_months,
            expected_milestones=expected,
            window_closing_in_months=window_closing,
            urgency_score=urgency,
            generated_at=datetime.now(timezone.utc),
        )
    
    # ==================== HELPER METHODS ====================
    
    def _build_historical_series(
        self, signals: list[Signal]
    ) -> dict[str, list[dict]]:
        """Build time series from signals."""
        series = {
            "revenue": [],
            "users": [],
            "team_size": [],
            "github_stars": [],
        }
        
        for signal in signals:
            ts = signal.source_timestamp
            payload = signal.payload
            
            if "arr" in payload:
                series["revenue"].append({
                    "timestamp": ts,
                    "value": float(payload["arr"])
                })
            
            if "users" in payload:
                series["users"].append({
                    "timestamp": ts,
                    "value": int(payload["users"])
                })
            
            if "team_size" in payload:
                series["team_size"].append({
                    "timestamp": ts,
                    "value": int(payload["team_size"])
                })
            
            if signal.record_type == "github_profile" and "total_stars" in payload:
                series["github_stars"].append({
                    "timestamp": ts,
                    "value": int(payload["total_stars"])
                })
        
        # Sort each series
        for key in series:
            series[key].sort(key=lambda x: x["timestamp"])
        
        return series
    
    def _forecast_revenue(
        self, history: dict, horizon_months: int
    ) -> dict[str, Any]:
        """Forecast revenue using exponential smoothing."""
        revenue_data = history.get("revenue", [])
        
        if len(revenue_data) < 2:
            return {"predicted": None, "confidence": "low"}
        
        # Extract values and timestamps
        values = [d["value"] for d in revenue_data]
        
        # Calculate growth rate
        growth_rates = []
        for i in range(len(values) - 1):
            if values[i] > 0:
                rate = (values[i + 1] - values[i]) / values[i]
                growth_rates.append(rate)
        
        if not growth_rates:
            return {"predicted": None, "confidence": "low"}
        
        # Use median growth rate for robustness
        median_growth = np.median(growth_rates)
        
        # Forecast forward
        last_value = values[-1]
        predictions = []
        lower_bounds = []
        upper_bounds = []
        
        current = last_value
        for month in range(1, horizon_months + 1):
            # Apply growth with decay (growth rates tend to slow)
            decay_factor = 0.95 ** month
            effective_growth = median_growth * decay_factor
            
            current = current * (1 + effective_growth)
            predictions.append(current)
            
            # Confidence intervals (±20% for simplicity)
            lower_bounds.append(current * 0.8)
            upper_bounds.append(current * 1.2)
        
        return {
            "predicted": predictions,
            "lower_bound": lower_bounds,
            "upper_bound": upper_bounds,
            "monthly_growth_rate": float(median_growth),
            "confidence": "medium" if len(values) >= 5 else "low"
        }
    
    def _forecast_users(
        self, history: dict, horizon_months: int
    ) -> dict[str, Any]:
        """Forecast user growth."""
        user_data = history.get("users", [])
        
        if len(user_data) < 2:
            return {"predicted": None, "confidence": "low"}
        
        values = [d["value"] for d in user_data]
        
        # Similar to revenue forecast
        growth_rates = []
        for i in range(len(values) - 1):
            if values[i] > 0:
                rate = (values[i + 1] - values[i]) / values[i]
                growth_rates.append(rate)
        
        if not growth_rates:
            return {"predicted": None, "confidence": "low"}
        
        median_growth = np.median(growth_rates)
        last_value = values[-1]
        predictions = []
        
        current = last_value
        for month in range(1, horizon_months + 1):
            decay_factor = 0.95 ** month
            effective_growth = median_growth * decay_factor
            current = current * (1 + effective_growth)
            predictions.append(int(current))
        
        return {
            "predicted": predictions,
            "monthly_growth_rate": float(median_growth),
            "confidence": "medium" if len(values) >= 5 else "low"
        }
    
    def _forecast_team_size(
        self, history: dict, horizon_months: int
    ) -> dict[str, Any]:
        """Forecast team size (typically linear)."""
        team_data = history.get("team_size", [])
        
        if len(team_data) < 2:
            return {"predicted": None, "confidence": "low"}
        
        values = [d["value"] for d in team_data]
        
        # Linear growth for team size
        total_growth = values[-1] - values[0]
        time_span_months = (
            team_data[-1]["timestamp"] - team_data[0]["timestamp"]
        ).days / 30
        
        if time_span_months == 0:
            return {"predicted": None, "confidence": "low"}
        
        monthly_growth = total_growth / time_span_months
        
        predictions = []
        current = values[-1]
        for month in range(1, horizon_months + 1):
            current += monthly_growth
            predictions.append(max(0, int(current)))
        
        return {
            "predicted": predictions,
            "monthly_growth": float(monthly_growth),
            "confidence": "medium"
        }
    
    def _detect_inflection_points(
        self, revenue_fc: dict, user_fc: dict, team_fc: dict
    ) -> list[dict[str, Any]]:
        """Identify predicted inflection points."""
        inflections = []
        
        # Revenue inflection (crossing key thresholds)
        if revenue_fc.get("predicted"):
            for i, val in enumerate(revenue_fc["predicted"]):
                # $1M ARR milestone
                if i > 0 and revenue_fc["predicted"][i-1] < 1_000_000 <= val:
                    inflections.append({
                        "type": "revenue_milestone",
                        "month": i + 1,
                        "description": "Crossing $1M ARR",
                        "value": val
                    })
                # $5M ARR milestone
                if i > 0 and revenue_fc["predicted"][i-1] < 5_000_000 <= val:
                    inflections.append({
                        "type": "revenue_milestone",
                        "month": i + 1,
                        "description": "Crossing $5M ARR",
                        "value": val
                    })
        
        # User growth inflection
        if user_fc.get("predicted"):
            for i, val in enumerate(user_fc["predicted"]):
                # 10K users
                if i > 0 and user_fc["predicted"][i-1] < 10_000 <= val:
                    inflections.append({
                        "type": "user_milestone",
                        "month": i + 1,
                        "description": "Reaching 10K users",
                        "value": val
                    })
                # 100K users
                if i > 0 and user_fc["predicted"][i-1] < 100_000 <= val:
                    inflections.append({
                        "type": "user_milestone",
                        "month": i + 1,
                        "description": "Reaching 100K users",
                        "value": val
                    })
        
        return inflections
    
    def _calculate_forecast_confidence(
        self, history: dict, horizon: int
    ) -> float:
        """Calculate confidence in forecast."""
        # More historical data = higher confidence
        total_points = sum(len(series) for series in history.values())
        data_confidence = min(1.0, total_points / 20)
        
        # Shorter horizons = higher confidence
        horizon_confidence = max(0.3, 1.0 - (horizon / 24))
        
        return (data_confidence + horizon_confidence) / 2
    
    def _extract_success_features(
        self, founder_id: int, signals: list[Signal]
    ) -> dict[str, Any]:
        """Extract features for success probability model."""
        founder = self.repo.get_founder(founder_id)
        
        features = {
            "signal_count": len(signals),
            "is_technical": founder.github_handle is not None,
            "is_cold_start": founder.is_cold_start,
            "signal_diversity": len(set(s.source for s in signals)),
        }
        
        # Extract current metrics
        for signal in signals:
            payload = signal.payload
            
            if "arr" in payload:
                features["current_arr"] = float(payload["arr"])
            if "users" in payload:
                features["current_users"] = int(payload["users"])
            if "team_size" in payload:
                features["current_team_size"] = int(payload["team_size"])
        
        # Calculate momentum
        series = self._build_historical_series(signals)
        if len(series.get("revenue", [])) >= 2:
            rev_vals = [d["value"] for d in series["revenue"]]
            features["revenue_momentum"] = (rev_vals[-1] - rev_vals[0]) / rev_vals[0] if rev_vals[0] > 0 else 0
        
        return features
    
    def _estimate_pmf_probability(self, features: dict) -> float:
        """Estimate probability of achieving product-market fit."""
        # Heuristic model (would be ML in production)
        prob = 0.5  # Base probability
        
        # Has revenue
        if features.get("current_arr", 0) > 100_000:
            prob += 0.2
        
        # Strong momentum
        if features.get("revenue_momentum", 0) > 0.2:  # >20% growth
            prob += 0.15
        
        # Technical founder
        if features.get("is_technical"):
            prob += 0.1
        
        # Good signal diversity
        if features.get("signal_diversity", 0) >= 4:
            prob += 0.05
        
        return min(1.0, max(0.0, prob))
    
    def _estimate_funding_probability(self, features: dict) -> float:
        """Estimate probability of raising Series A."""
        prob = 0.3  # Base
        
        # Strong metrics = higher funding probability
        if features.get("current_arr", 0) > 1_000_000:
            prob += 0.3
        if features.get("current_users", 0) > 10_000:
            prob += 0.2
        if features.get("revenue_momentum", 0) > 0.3:
            prob += 0.2
        
        return min(1.0, prob)
    
    def _estimate_profitability_probability(self, features: dict) -> float:
        """Estimate probability of reaching profitability."""
        prob = 0.2  # Base (harder milestone)
        
        if features.get("current_arr", 0) > 500_000:
            prob += 0.3
        if features.get("current_team_size", 0) < 10:  # Lean team
            prob += 0.2
        
        return min(1.0, prob)
    
    def _estimate_exit_probability(self, features: dict) -> float:
        """Estimate exit potential (acquisition/IPO)."""
        prob = 0.1  # Base (rare event)
        
        if features.get("current_arr", 0) > 5_000_000:
            prob += 0.3
        if features.get("revenue_momentum", 0) > 0.5:
            prob += 0.2
        
        return min(1.0, prob)
    
    def _identify_key_drivers(self, features: dict) -> list[str]:
        """Identify key success drivers."""
        drivers = []
        
        if features.get("revenue_momentum", 0) > 0.2:
            drivers.append("Strong revenue momentum")
        if features.get("is_technical"):
            drivers.append("Technical founder (can execute)")
        if features.get("signal_diversity", 0) >= 4:
            drivers.append("Rich data from multiple sources")
        if features.get("current_users", 0) > 1000:
            drivers.append("Proven user traction")
        
        return drivers
    
    def _identify_risk_factors(self, features: dict) -> list[str]:
        """Identify risk factors."""
        risks = []
        
        if features.get("is_cold_start"):
            risks.append("Cold-start founder (limited track record)")
        if features.get("signal_count", 0) < 5:
            risks.append("Limited data for assessment")
        if features.get("current_arr", 0) == 0:
            risks.append("No revenue yet")
        
        return risks
    
    def _estimate_time_to_pmf(self, features: dict) -> int | None:
        """Estimate months to product-market fit."""
        # Heuristic based on current state
        if features.get("current_users", 0) > 1000:
            return 3  # Close to PMF
        elif features.get("current_users", 0) > 100:
            return 6  # Making progress
        else:
            return 12  # Early stage
    
    def _estimate_time_to_funding(self, features: dict) -> int | None:
        """Estimate months to Series A readiness."""
        if features.get("current_arr", 0) > 500_000:
            return 6
        elif features.get("current_arr", 0) > 100_000:
            return 12
        else:
            return 24
    
    def _calculate_probability_confidence(self, signals: list[Signal]) -> float:
        """Calculate confidence in probability estimates."""
        # More signals = higher confidence
        return min(1.0, len(signals) / 15)
    
    def _assess_execution_risk(
        self, signals: list[Signal], founder: Founder
    ) -> float:
        """Assess execution risk (0-1, higher = more risk)."""
        risk = 0.5  # Base
        
        # Technical founders execute better
        if founder.github_handle:
            risk -= 0.2
        
        # Recent activity = good execution
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        recent = []
        for s in signals:
            ts = s.source_timestamp
            # Make timestamp timezone-aware if it isn't
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if (now - ts).days <= 90:
                recent.append(s)
        
        if len(recent) >= 3:
            risk -= 0.2
        elif len(recent) == 0:
            risk += 0.3
        
        return max(0.0, min(1.0, risk))
    
    def _assess_market_timing_risk(self, signals: list[Signal]) -> float:
        """Assess market timing risk."""
        # Would check market trends, competitor activity
        # Placeholder: moderate risk
        return 0.4
    
    def _assess_team_risk(
        self, signals: list[Signal], founder: Founder
    ) -> float:
        """Assess team-related risk."""
        risk = 0.5
        
        # Single founder = higher risk
        team_signals = [s for s in signals if "team" in str(s.payload)]
        if not team_signals:
            risk += 0.2
        
        # Cold-start = less experience
        if founder.is_cold_start:
            risk += 0.15
        
        return min(1.0, risk)
    
    def _assess_competitive_risk(self, signals: list[Signal]) -> float:
        """Assess competitive landscape risk."""
        # Would analyze competitor signals
        return 0.5  # Moderate default
    
    def _assess_financial_risk(self, signals: list[Signal]) -> float:
        """Assess financial/runway risk."""
        risk = 0.5
        
        # Check for revenue
        has_revenue = any("arr" in s.payload or "mrr" in s.payload for s in signals)
        if has_revenue:
            risk -= 0.3
        else:
            risk += 0.2
        
        return max(0.0, min(1.0, risk))
    
    def _compile_risk_factors(
        self, exec_risk: float, market_risk: float, team_risk: float,
        comp_risk: float, fin_risk: float, signals: list[Signal]
    ) -> list[dict[str, Any]]:
        """Compile detailed risk factors."""
        factors = []
        
        if exec_risk > 0.6:
            factors.append({
                "category": "execution",
                "severity": "high",
                "description": "High execution risk - limited recent activity or technical capability"
            })
        
        if team_risk > 0.6:
            factors.append({
                "category": "team",
                "severity": "high",
                "description": "Team composition risk - may lack key skills or experience"
            })
        
        if fin_risk > 0.6:
            factors.append({
                "category": "financial",
                "severity": "high",
                "description": "Financial risk - no revenue or unclear path to sustainability"
            })
        
        return factors
    
    def _suggest_mitigations(
        self, risk_factors: list[dict[str, Any]]
    ) -> list[str]:
        """Suggest risk mitigation strategies."""
        suggestions = []
        
        for factor in risk_factors:
            if factor["category"] == "execution":
                suggestions.append("Closely monitor milestones; consider hands-on support")
            elif factor["category"] == "team":
                suggestions.append("Recommend key hires; connect with advisors")
            elif factor["category"] == "financial":
                suggestions.append("Ensure sufficient runway; focus on revenue milestones")
        
        return suggestions
    
    def _empty_forecast(
        self, founder_id: int, horizon: int
    ) -> TrajectoryForecast:
        """Empty forecast when no data."""
        return TrajectoryForecast(
            founder_id=founder_id,
            horizon_months=horizon,
            revenue_forecast={"predicted": None, "confidence": "none"},
            user_growth_forecast={"predicted": None, "confidence": "none"},
            team_size_forecast={"predicted": None, "confidence": "none"},
            inflection_points=[],
            confidence=0.0,
            model_used="none",
            generated_at=datetime.now(timezone.utc),
        )
    
    def _empty_success_prob(self, founder_id: int) -> SuccessProbability:
        """Empty success probability when no data."""
        return SuccessProbability(
            founder_id=founder_id,
            product_market_fit_prob=0.0,
            series_a_funding_prob=0.0,
            profitability_prob=0.0,
            exit_potential_prob=0.0,
            key_drivers=[],
            risk_factors=["No data available"],
            expected_months_to_pmf=None,
            expected_months_to_funding=None,
            confidence=0.0,
            generated_at=datetime.now(timezone.utc),
        )
    
    def _empty_risk_assessment(self, founder_id: int) -> RiskAssessment:
        """Empty risk assessment when no data."""
        # Absence of evidence is NOT evidence of risk. Returning 1.0 here would
        # brand every cold-start founder "critical" and violate the guarantee
        # that a founder is never defaulted to a bad score for lacking a
        # traditional paper trail. `risk_level="unknown"` forces the caller (and
        # the UI) to treat this as undetermined rather than as a finding.
        return RiskAssessment(
            founder_id=founder_id,
            execution_risk=0.0,
            market_timing_risk=0.0,
            team_risk=0.0,
            competitive_risk=0.0,
            financial_risk=0.0,
            overall_risk=0.0,
            risk_level="unknown",
            risk_factors=[{
                "category": "data",
                "severity": "info",
                "description": "No signals ingested yet — risk is undetermined, not low and not high."
            }],
            mitigation_suggestions=["Ingest signals (deck, GitHub, web) to enable risk assessment."],
            generated_at=datetime.now(timezone.utc),
        )
