"""Signal correlation and analysis engine.

Cross-analyzes signals from multiple sources to find patterns, contradictions,
momentum, and quality indicators. Goes beyond simple storage to extract intelligence.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models.signal import Signal


@dataclass
class Contradiction:
    """A detected inconsistency between signals."""
    metric: str
    values: list[dict[str, Any]]
    severity: str  # low, medium, high, critical
    explanation: str
    sources: list[str]
    confidence: float


@dataclass
class MomentumIndicator:
    """Detected momentum in a specific dimension."""
    dimension: str  # github_stars, revenue, team, users, etc.
    direction: str  # accelerating, steady, decelerating, stagnant
    velocity: float  # rate of change
    datapoints: list[dict[str, Any]]
    timespan_days: int
    confidence: float


@dataclass
class QualitySignal:
    """Quality indicators extracted from signals."""
    indicator: str
    score: float  # 0-1
    evidence: list[str]
    weight: float  # importance weight


@dataclass
class NetworkEffect:
    """Network effects and ecosystem signals."""
    effect_type: str  # contributors, forks, mentions, endorsements
    strength: float  # 0-1
    participants: list[str]
    evidence: list[str]


@dataclass
class CorrelationReport:
    """Complete signal correlation analysis."""
    founder_id: int
    consistency_score: float  # 0-1, how consistent are claims?
    contradictions: list[Contradiction]
    momentum_indicators: list[MomentumIndicator]
    quality_signals: list[QualitySignal]
    network_effects: list[NetworkEffect]
    confidence: float  # overall data quality confidence
    red_flags: list[str]
    green_flags: list[str]
    analyzed_signal_count: int
    generated_at: datetime


class SignalCorrelationEngine:
    """Analyzes signals to extract intelligence and detect patterns."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)
    
    def analyze_founder_signals(self, founder_id: int) -> CorrelationReport:
        """Complete correlation analysis for a founder."""
        signals = self.repo.signals_for(founder_id)
        
        if not signals:
            return self._empty_report(founder_id)
        
        # Run all analysis modules
        contradictions = self.find_contradictions(signals)
        momentum = self.detect_momentum(signals)
        quality = self.extract_quality_signals(signals)
        network = self.analyze_network_effects(signals)
        consistency = self.calculate_consistency(signals, contradictions)
        red_flags, green_flags = self.identify_flags(
            signals, contradictions, momentum, quality
        )
        
        return CorrelationReport(
            founder_id=founder_id,
            consistency_score=consistency,
            contradictions=contradictions,
            momentum_indicators=momentum,
            quality_signals=quality,
            network_effects=network,
            confidence=self._calculate_overall_confidence(signals, contradictions),
            red_flags=red_flags,
            green_flags=green_flags,
            analyzed_signal_count=len(signals),
            generated_at=datetime.now(timezone.utc),
        )
    
    def find_contradictions(self, signals: list[Signal]) -> list[Contradiction]:
        """Cross-check claims across sources for inconsistencies."""
        contradictions = []
        
        # Extract all quantitative claims by metric
        metrics = self._extract_all_metrics(signals)
        
        for metric_name, values in metrics.items():
            if len(values) < 2:
                continue  # Need at least 2 sources to contradict
            
            # Check for significant variance
            variance = self._calculate_variance(values)
            
            if variance > 0.3:  # >30% variance is suspicious
                severity = self._assess_severity(metric_name, variance)
                
                contradictions.append(
                    Contradiction(
                        metric=metric_name,
                        values=values,
                        severity=severity,
                        explanation=self._explain_contradiction(
                            metric_name, values, variance
                        ),
                        sources=[v["source"] for v in values],
                        confidence=min(1.0, variance),
                    )
                )
        
        # Check temporal consistency (retroactive changes are red flags)
        temporal_contradictions = self._check_temporal_consistency(signals)
        contradictions.extend(temporal_contradictions)
        
        return contradictions
    
    def detect_momentum(self, signals: list[Signal]) -> list[MomentumIndicator]:
        """Detect momentum across time-series signals."""
        momentum_indicators = []
        
        # Group signals by dimension (GitHub, revenue, users, etc.)
        time_series = self._build_time_series(signals)
        
        for dimension, datapoints in time_series.items():
            if len(datapoints) < 3:
                continue  # Need at least 3 points for trend
            
            # Calculate velocity and acceleration
            direction, velocity = self._calculate_momentum(datapoints)
            
            if direction != "insufficient_data":
                timespan = (
                    datapoints[-1]["timestamp"] - datapoints[0]["timestamp"]
                ).days
                
                momentum_indicators.append(
                    MomentumIndicator(
                        dimension=dimension,
                        direction=direction,
                        velocity=velocity,
                        datapoints=datapoints,
                        timespan_days=timespan,
                        confidence=self._momentum_confidence(datapoints),
                    )
                )
        
        return momentum_indicators
    
    def extract_quality_signals(self, signals: list[Signal]) -> list[QualitySignal]:
        """Extract quality indicators from signals."""
        quality_signals = []
        
        # GitHub code quality
        github_signals = [s for s in signals if s.source == "github"]
        if github_signals:
            quality_signals.extend(self._analyze_github_quality(github_signals))
        
        # Communication quality (from deck, web, etc.)
        comm_signals = [
            s for s in signals 
            if s.source in ("deck", "web", "tavily")
        ]
        if comm_signals:
            quality_signals.extend(self._analyze_communication_quality(comm_signals))
        
        # Execution quality (consistency, follow-through)
        quality_signals.append(self._analyze_execution_quality(signals))
        
        return quality_signals
    
    def analyze_network_effects(self, signals: list[Signal]) -> list[NetworkEffect]:
        """Analyze network effects and ecosystem signals."""
        network_effects = []
        
        # GitHub collaborators
        github_network = self._extract_github_network(signals)
        if github_network:
            network_effects.append(github_network)
        
        # Social proof (mentions, endorsements)
        social_proof = self._extract_social_proof(signals)
        if social_proof:
            network_effects.append(social_proof)
        
        # Community contributions
        community = self._extract_community_signals(signals)
        if community:
            network_effects.append(community)
        
        return network_effects
    
    # Helper methods
    
    def _extract_all_metrics(
        self, signals: list[Signal]
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract all quantitative metrics from signals."""
        metrics = defaultdict(list)
        
        for signal in signals:
            payload = signal.payload
            
            # Revenue metrics
            if "arr" in payload:
                metrics["arr"].append({
                    "value": float(payload["arr"]),
                    "source": signal.source,
                    "timestamp": signal.source_timestamp,
                    "confidence": signal.confidence,
                })
            
            if "mrr" in payload:
                metrics["mrr"].append({
                    "value": float(payload["mrr"]),
                    "source": signal.source,
                    "timestamp": signal.source_timestamp,
                    "confidence": signal.confidence,
                })
            
            # User metrics
            if "users" in payload or "user_count" in payload:
                metrics["users"].append({
                    "value": int(payload.get("users", payload.get("user_count"))),
                    "source": signal.source,
                    "timestamp": signal.source_timestamp,
                    "confidence": signal.confidence,
                })
            
            # Team size
            if "team_size" in payload or "employees" in payload:
                metrics["team_size"].append({
                    "value": int(payload.get("team_size", payload.get("employees"))),
                    "source": signal.source,
                    "timestamp": signal.source_timestamp,
                    "confidence": signal.confidence,
                })
            
            # GitHub stars (from profile)
            if signal.record_type == "github_profile" and "total_stars" in payload:
                metrics["github_stars"].append({
                    "value": int(payload["total_stars"]),
                    "source": signal.source,
                    "timestamp": signal.source_timestamp,
                    "confidence": signal.confidence,
                })
            
            # Funding raised
            if "funding_raised" in payload or "raised" in payload:
                metrics["funding"].append({
                    "value": float(payload.get("funding_raised", payload.get("raised"))),
                    "source": signal.source,
                    "timestamp": signal.source_timestamp,
                    "confidence": signal.confidence,
                })
        
        return metrics
    
    def _calculate_variance(self, values: list[dict[str, Any]]) -> float:
        """Calculate coefficient of variation for a metric."""
        if len(values) < 2:
            return 0.0
        
        nums = [v["value"] for v in values]
        mean = sum(nums) / len(nums)
        
        if mean == 0:
            return 0.0
        
        # Coefficient of variation (std / mean)
        variance = sum((x - mean) ** 2 for x in nums) / len(nums)
        std_dev = variance ** 0.5
        cv = std_dev / mean
        
        return cv
    
    def _assess_severity(self, metric: str, variance: float) -> str:
        """Assess contradiction severity based on metric type and variance."""
        # Revenue/funding contradictions are critical
        if metric in ("arr", "mrr", "funding"):
            if variance > 0.5:
                return "critical"
            elif variance > 0.3:
                return "high"
            else:
                return "medium"
        
        # User count contradictions are high priority
        if metric in ("users", "customers"):
            if variance > 0.7:
                return "high"
            elif variance > 0.4:
                return "medium"
            else:
                return "low"
        
        # GitHub stars less critical (can fluctuate)
        if metric == "github_stars":
            if variance > 0.8:
                return "medium"
            else:
                return "low"
        
        # Default
        if variance > 0.6:
            return "high"
        elif variance > 0.4:
            return "medium"
        else:
            return "low"
    
    def _explain_contradiction(
        self, metric: str, values: list[dict], variance: float
    ) -> str:
        """Generate human-readable contradiction explanation."""
        sorted_vals = sorted(values, key=lambda x: x["value"])
        low = sorted_vals[0]
        high = sorted_vals[-1]
        
        diff_pct = ((high["value"] - low["value"]) / low["value"] * 100) if low["value"] > 0 else 0
        
        return (
            f"{metric.upper()} varies significantly: "
            f"{low['source']} reports {low['value']:,.0f}, "
            f"but {high['source']} reports {high['value']:,.0f} "
            f"({diff_pct:.0f}% difference). "
            f"Verify which source is authoritative."
        )
    
    def _check_temporal_consistency(
        self, signals: list[Signal]
    ) -> list[Contradiction]:
        """Check for retroactive changes (red flag)."""
        contradictions = []
        
        # Group by record type
        by_type = defaultdict(list)
        for signal in signals:
            by_type[signal.record_type].append(signal)
        
        # Check each type for temporal inconsistencies
        for record_type, sigs in by_type.items():
            if len(sigs) < 2:
                continue
            
            # Sort by ingestion time
            sorted_sigs = sorted(sigs, key=lambda s: s.ingested_at)
            
            # Check if earlier ingestion has later source timestamp (retroactive edit)
            for i in range(len(sorted_sigs) - 1):
                if sorted_sigs[i].source_timestamp > sorted_sigs[i + 1].source_timestamp:
                    contradictions.append(
                        Contradiction(
                            metric="temporal_consistency",
                            values=[
                                {
                                    "source": sorted_sigs[i].source,
                                    "source_time": sorted_sigs[i].source_timestamp,
                                    "ingested": sorted_sigs[i].ingested_at,
                                },
                                {
                                    "source": sorted_sigs[i + 1].source,
                                    "source_time": sorted_sigs[i + 1].source_timestamp,
                                    "ingested": sorted_sigs[i + 1].ingested_at,
                                },
                            ],
                            severity="high",
                            explanation=(
                                f"Temporal inconsistency detected in {record_type}: "
                                "later-ingested signal has earlier source timestamp. "
                                "Possible retroactive data manipulation."
                            ),
                            sources=[sorted_sigs[i].source, sorted_sigs[i + 1].source],
                            confidence=0.9,
                        )
                    )
        
        return contradictions
    
    def _build_time_series(
        self, signals: list[Signal]
    ) -> dict[str, list[dict[str, Any]]]:
        """Build time series for different dimensions."""
        time_series = defaultdict(list)
        
        for signal in signals:
            payload = signal.payload
            ts = signal.source_timestamp
            
            # GitHub stars over time
            if signal.record_type == "github_profile" and "total_stars" in payload:
                time_series["github_stars"].append({
                    "timestamp": ts,
                    "value": int(payload["total_stars"]),
                })
            
            # Repo stars over time (per repo)
            if signal.record_type == "github_repo" and "stars" in payload:
                time_series["repo_stars"].append({
                    "timestamp": ts,
                    "value": int(payload["stars"]),
                    "repo": payload.get("name"),
                })
            
            # Revenue over time
            if "arr" in payload:
                time_series["arr"].append({
                    "timestamp": ts,
                    "value": float(payload["arr"]),
                })
            
            # Users over time
            if "users" in payload:
                time_series["users"].append({
                    "timestamp": ts,
                    "value": int(payload["users"]),
                })
            
            # Team size over time
            if "team_size" in payload:
                time_series["team_size"].append({
                    "timestamp": ts,
                    "value": int(payload["team_size"]),
                })
        
        # Sort each series by timestamp
        for key in time_series:
            time_series[key].sort(key=lambda x: x["timestamp"])
        
        return time_series
    
    def _calculate_momentum(
        self, datapoints: list[dict]
    ) -> tuple[str, float]:
        """Calculate momentum direction and velocity."""
        if len(datapoints) < 2:
            return "insufficient_data", 0.0
        
        # Calculate velocities between consecutive points
        velocities = []
        for i in range(len(datapoints) - 1):
            dt = (datapoints[i + 1]["timestamp"] - datapoints[i]["timestamp"]).days
            if dt == 0:
                continue
            
            dv = datapoints[i + 1]["value"] - datapoints[i]["value"]
            velocity = dv / dt  # change per day
            velocities.append(velocity)
        
        if not velocities:
            return "insufficient_data", 0.0
        
        avg_velocity = sum(velocities) / len(velocities)
        
        # Check if velocity is accelerating
        if len(velocities) >= 2:
            recent_velocity = sum(velocities[-2:]) / 2
            older_velocity = sum(velocities[:-2]) / len(velocities[:-2]) if len(velocities) > 2 else velocities[0]
            
            if recent_velocity > older_velocity * 1.2:
                return "accelerating", avg_velocity
            elif recent_velocity < older_velocity * 0.8:
                return "decelerating", avg_velocity
        
        # Check overall direction
        if avg_velocity > 0.01:
            return "steady_growth", avg_velocity
        elif avg_velocity < -0.01:
            return "declining", avg_velocity
        else:
            return "stagnant", avg_velocity
    
    def _momentum_confidence(self, datapoints: list[dict]) -> float:
        """Calculate confidence in momentum assessment."""
        # More datapoints = higher confidence
        point_confidence = min(1.0, len(datapoints) / 10)
        
        # Longer timespan = higher confidence
        timespan = (datapoints[-1]["timestamp"] - datapoints[0]["timestamp"]).days
        time_confidence = min(1.0, timespan / 180)  # 6 months = full confidence
        
        # Combine
        return (point_confidence + time_confidence) / 2
    
    def _analyze_github_quality(
        self, github_signals: list[Signal]
    ) -> list[QualitySignal]:
        """Analyze GitHub signal quality."""
        quality_signals = []
        
        # Consistency of contributions (regular commits vs. sporadic)
        profile_signals = [
            s for s in github_signals if s.record_type == "github_profile"
        ]
        if profile_signals:
            latest = profile_signals[-1]
            repos = latest.payload.get("original_repos", 0)
            
            if repos > 0:
                consistency_score = min(1.0, repos / 10)
                quality_signals.append(
                    QualitySignal(
                        indicator="github_consistency",
                        score=consistency_score,
                        evidence=[f"{repos} original repositories"],
                        weight=0.3,
                    )
                )
        
        # Repository quality (stars per repo, documentation, etc.)
        repo_signals = [s for s in github_signals if s.record_type == "github_repo"]
        if repo_signals:
            avg_stars = sum(s.payload.get("stars", 0) for s in repo_signals) / len(repo_signals)
            has_docs = sum(
                1 for s in repo_signals 
                if s.payload.get("description") and len(s.payload["description"]) > 20
            ) / len(repo_signals)
            
            quality_score = min(1.0, (avg_stars / 50) * 0.5 + has_docs * 0.5)
            quality_signals.append(
                QualitySignal(
                    indicator="repo_quality",
                    score=quality_score,
                    evidence=[
                        f"Average {avg_stars:.0f} stars per repo",
                        f"{has_docs*100:.0f}% repos have descriptions",
                    ],
                    weight=0.4,
                )
            )
        
        return quality_signals
    
    def _analyze_communication_quality(
        self, comm_signals: list[Signal]
    ) -> list[QualitySignal]:
        """Analyze communication quality from text signals."""
        quality_signals = []
        
        # Extract all text
        texts = []
        for signal in comm_signals:
            if hasattr(signal, 'text') and signal.text:
                texts.append(signal.text)
            elif "text" in signal.payload:
                texts.append(signal.payload["text"])
        
        if not texts:
            return quality_signals
        
        # Analyze clarity (longer, well-structured text = better communication)
        avg_length = sum(len(t) for t in texts) / len(texts)
        clarity_score = min(1.0, avg_length / 500)  # 500 chars = good clarity
        
        quality_signals.append(
            QualitySignal(
                indicator="communication_clarity",
                score=clarity_score,
                evidence=[f"Average {avg_length:.0f} characters per communication"],
                weight=0.2,
            )
        )
        
        return quality_signals
    
    def _analyze_execution_quality(self, signals: list[Signal]) -> QualitySignal:
        """Analyze execution quality (consistency, follow-through)."""
        # High signal count = good execution (gathering evidence)
        signal_count = len(signals)
        
        # Signal recency (recent signals = active execution)
        now = datetime.now(timezone.utc)
        recent_signals = []
        for s in signals:
            ts = s.source_timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if (now - ts).days <= 90:
                recent_signals.append(s)
        
        recency_ratio = len(recent_signals) / signal_count if signal_count > 0 else 0
        
        # Diversity of signal sources (more sources = better)
        unique_sources = len(set(s.source for s in signals))
        diversity_score = min(1.0, unique_sources / 5)
        
        # Combined execution score
        execution_score = (
            min(1.0, signal_count / 20) * 0.4 +
            recency_ratio * 0.3 +
            diversity_score * 0.3
        )
        
        return QualitySignal(
            indicator="execution_quality",
            score=execution_score,
            evidence=[
                f"{signal_count} total signals",
                f"{len(recent_signals)} recent (90 days)",
                f"{unique_sources} unique sources",
            ],
            weight=0.5,
        )
    
    def _extract_github_network(self, signals: list[Signal]) -> NetworkEffect | None:
        """Extract GitHub collaboration network."""
        github_signals = [s for s in signals if s.source == "github"]
        if not github_signals:
            return None
        
        # Extract collaborator count from repo forks/contributors
        total_forks = sum(
            s.payload.get("forks", 0) 
            for s in github_signals 
            if s.record_type == "github_repo"
        )
        
        if total_forks == 0:
            return None
        
        strength = min(1.0, total_forks / 20)  # 20+ forks = strong network
        
        return NetworkEffect(
            effect_type="github_collaboration",
            strength=strength,
            participants=[],  # Would need GitHub API to get actual collaborators
            evidence=[f"{total_forks} total forks across repositories"],
        )
    
    def _extract_social_proof(self, signals: list[Signal]) -> NetworkEffect | None:
        """Extract social proof from various signals."""
        # Count mentions across sources
        mention_count = 0
        sources = []
        
        for signal in signals:
            if signal.source in ("tavily", "web", "producthunt"):
                mention_count += 1
                sources.append(signal.source)
        
        if mention_count == 0:
            return None
        
        strength = min(1.0, mention_count / 10)
        
        return NetworkEffect(
            effect_type="social_proof",
            strength=strength,
            participants=[],
            evidence=[f"{mention_count} mentions across {len(set(sources))} platforms"],
        )
    
    def _extract_community_signals(self, signals: list[Signal]) -> NetworkEffect | None:
        """Extract community contribution signals."""
        # Check for community-related signals
        community_signals = [
            s for s in signals 
            if any(kw in s.record_type for kw in ["community", "contribution", "stackoverflow"])
        ]
        
        if not community_signals:
            return None
        
        strength = min(1.0, len(community_signals) / 5)
        
        return NetworkEffect(
            effect_type="community_engagement",
            strength=strength,
            participants=[],
            evidence=[f"{len(community_signals)} community contributions"],
        )
    
    def calculate_consistency(
        self, signals: list[Signal], contradictions: list[Contradiction]
    ) -> float:
        """Calculate overall consistency score (0-1)."""
        if not signals:
            return 0.0
        
        # Start with base consistency
        base = 1.0
        
        # Penalize for contradictions
        critical_count = sum(1 for c in contradictions if c.severity == "critical")
        high_count = sum(1 for c in contradictions if c.severity == "high")
        medium_count = sum(1 for c in contradictions if c.severity == "medium")
        
        penalty = (
            critical_count * 0.3 +
            high_count * 0.15 +
            medium_count * 0.05
        )
        
        return max(0.0, base - penalty)
    
    def _calculate_overall_confidence(
        self, signals: list[Signal], contradictions: list[Contradiction]
    ) -> float:
        """Calculate overall data quality confidence."""
        # More signals = higher confidence (up to a point)
        signal_confidence = min(1.0, len(signals) / 30)
        
        # Verified sources boost confidence
        verified_ratio = sum(
            1 for s in signals if s.confidence == "verified"
        ) / len(signals) if signals else 0
        
        # Contradictions reduce confidence
        contradiction_penalty = len(contradictions) * 0.1
        
        confidence = (
            signal_confidence * 0.4 +
            verified_ratio * 0.4 +
            (1.0 - min(0.2, contradiction_penalty)) * 0.2
        )
        
        return max(0.0, min(1.0, confidence))
    
    def identify_flags(
        self,
        signals: list[Signal],
        contradictions: list[Contradiction],
        momentum: list[MomentumIndicator],
        quality: list[QualitySignal],
    ) -> tuple[list[str], list[str]]:
        """Identify red flags and green flags."""
        red_flags = []
        green_flags = []
        
        # Red flags from contradictions
        critical_contradictions = [c for c in contradictions if c.severity in ("critical", "high")]
        if critical_contradictions:
            red_flags.append(
                f"⚠️ {len(critical_contradictions)} critical data contradictions detected"
            )
        
        # Red flag: Too few signals
        if len(signals) < 5:
            red_flags.append("⚠️ Insufficient data for reliable assessment (<5 signals)")
        
        # Red flag: No recent activity
        now = datetime.now(timezone.utc)
        recent = []
        for s in signals:
            ts = s.source_timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if (now - ts).days <= 90:
                recent.append(s)
        
        if not recent:
            red_flags.append("⚠️ No recent activity in past 90 days")
        
        # Red flag: Declining momentum
        declining = [m for m in momentum if m.direction == "decelerating"]
        if declining:
            red_flags.append(
                f"⚠️ Declining momentum in: {', '.join(m.dimension for m in declining)}"
            )
        
        # Green flags from momentum
        accelerating = [m for m in momentum if m.direction == "accelerating"]
        if accelerating:
            green_flags.append(
                f"✅ Accelerating momentum in: {', '.join(m.dimension for m in accelerating)}"
            )
        
        # Green flag: High quality signals
        high_quality = [q for q in quality if q.score > 0.7]
        if high_quality:
            green_flags.append(
                f"✅ High quality indicators: {', '.join(q.indicator for q in high_quality)}"
            )
        
        # Green flag: Many verified sources
        verified_count = sum(1 for s in signals if s.confidence == "verified")
        if verified_count >= 5:
            green_flags.append(f"✅ {verified_count} verified data sources")
        
        # Green flag: Consistent data
        if not contradictions:
            green_flags.append("✅ All data sources consistent (no contradictions)")
        
        return red_flags, green_flags
    
    def _empty_report(self, founder_id: int) -> CorrelationReport:
        """Return empty report when no signals available."""
        return CorrelationReport(
            founder_id=founder_id,
            consistency_score=0.0,
            contradictions=[],
            momentum_indicators=[],
            quality_signals=[],
            network_effects=[],
            confidence=0.0,
            red_flags=["⚠️ No signals available for analysis"],
            green_flags=[],
            analyzed_signal_count=0,
            generated_at=datetime.now(timezone.utc),
        )
