"""Anomaly detection for identifying red flags and suspicious patterns.

Uses statistical methods to detect:
- Unusual metric patterns
- Behavioral anomalies
- Temporal inconsistencies
- Network anomalies
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models.founder import Founder
from app.models.signal import Signal


@dataclass
class Anomaly:
    """A detected anomaly."""
    anomaly_type: str  # statistical, behavioral, temporal, network
    severity: str  # low, medium, high, critical
    description: str
    evidence: list[str]
    confidence: float  # 0-1
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnomalyReport:
    """Complete anomaly detection report."""
    founder_id: int
    statistical_anomalies: list[Anomaly]
    behavioral_anomalies: list[Anomaly]
    temporal_anomalies: list[Anomaly]
    network_anomalies: list[Anomaly]
    overall_risk_level: str  # low, medium, high, critical
    recommended_action: str  # proceed, investigate, flag, reject
    anomaly_count: int
    generated_at: datetime


class AnomalyDetector:
    """Detects anomalies and red flags in founder data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)
    
    def detect_anomalies(self, founder_id: int) -> AnomalyReport:
        """Run complete anomaly detection analysis."""
        signals = self.repo.signals_for(founder_id)
        founder = self.repo.get_founder(founder_id)
        
        if not signals:
            return self._empty_report(founder_id)
        
        # Run detection across all dimensions
        statistical = self.detect_statistical_anomalies(signals)
        behavioral = self.detect_behavioral_anomalies(signals, founder)
        temporal = self.detect_temporal_anomalies(signals)
        network = self.detect_network_anomalies(founder_id, signals)
        
        # Aggregate risk
        all_anomalies = statistical + behavioral + temporal + network
        risk_level = self._calculate_risk_level(all_anomalies)
        action = self._recommend_action(risk_level, all_anomalies)
        
        return AnomalyReport(
            founder_id=founder_id,
            statistical_anomalies=statistical,
            behavioral_anomalies=behavioral,
            temporal_anomalies=temporal,
            network_anomalies=network,
            overall_risk_level=risk_level,
            recommended_action=action,
            anomaly_count=len(all_anomalies),
            generated_at=datetime.now(timezone.utc),
        )
    
    def detect_statistical_anomalies(self, signals: list[Signal]) -> list[Anomaly]:
        """Detect statistical outliers in metrics."""
        anomalies = []
        
        # Extract metrics
        metrics = self._extract_metrics(signals)
        
        # Check each metric against peer benchmarks
        for metric_name, values in metrics.items():
            if len(values) < 2:
                continue
            
            # Simple outlier detection using IQR method
            vals = np.array(values)
            q25, q75 = np.percentile(vals, [25, 75])
            iqr = q75 - q25
            
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            
            outliers = vals[(vals < lower_bound) | (vals > upper_bound)]
            
            if len(outliers) > 0:
                severity = "high" if len(outliers) > len(vals) / 2 else "medium"
                
                anomalies.append(Anomaly(
                    anomaly_type="statistical",
                    severity=severity,
                    description=f"{metric_name} shows unusual variance",
                    evidence=[
                        f"{len(outliers)} outlier values detected",
                        f"Range: {vals.min():.0f} - {vals.max():.0f}",
                        f"Expected range: {lower_bound:.0f} - {upper_bound:.0f}"
                    ],
                    confidence=min(0.9, len(outliers) / len(vals) + 0.5)
                ))
        
        # Check for too-good-to-be-true patterns
        tgtbt = self._check_too_good_to_be_true(metrics)
        anomalies.extend(tgtbt)
        
        return anomalies
    
    def detect_behavioral_anomalies(
        self, signals: list[Signal], founder: Founder
    ) -> list[Anomaly]:
        """Detect unusual behavioral patterns."""
        anomalies = []
        
        # GitHub activity spikes (gaming the system?)
        github_signals = [s for s in signals if s.source == "github"]
        if len(github_signals) >= 2:
            # Check for sudden star increases
            star_counts = []
            for sig in github_signals:
                if sig.record_type == "github_profile":
                    stars = sig.payload.get("total_stars", 0)
                    star_counts.append((sig.source_timestamp, stars))
            
            if len(star_counts) >= 2:
                star_counts.sort(key=lambda x: x[0])
                
                for i in range(len(star_counts) - 1):
                    time_diff_days = (star_counts[i+1][0] - star_counts[i][0]).days
                    star_diff = star_counts[i+1][1] - star_counts[i][1]
                    
                    if time_diff_days > 0:
                        daily_increase = star_diff / time_diff_days
                        
                        # Flag if >50 stars/day (suspicious for most projects)
                        if daily_increase > 50:
                            anomalies.append(Anomaly(
                                anomaly_type="behavioral",
                                severity="high",
                                description="Unusual GitHub star velocity",
                                evidence=[
                                    f"{daily_increase:.0f} stars/day increase",
                                    "Possible artificial inflation",
                                    f"Period: {star_counts[i][0].date()} to {star_counts[i+1][0].date()}"
                                ],
                                confidence=0.7
                            ))
        
        # Inconsistent founder history (frequent pivots)
        if len(signals) > 5:
            sector_mentions = set()
            for sig in signals:
                payload_str = str(sig.payload)
                # Simple sector detection (would be more sophisticated in production)
                sectors = ["AI", "FinTech", "HealthTech", "SaaS", "E-commerce"]
                for sector in sectors:
                    if sector.lower() in payload_str.lower():
                        sector_mentions.add(sector)
            
            if len(sector_mentions) > 3:
                anomalies.append(Anomaly(
                    anomaly_type="behavioral",
                    severity="medium",
                    description="Multiple sector pivots detected",
                    evidence=[
                        f"Active in {len(sector_mentions)} different sectors",
                        f"Sectors: {', '.join(sector_mentions)}",
                        "May indicate lack of focus"
                    ],
                    confidence=0.6
                ))
        
        return anomalies
    
    def detect_temporal_anomalies(self, signals: list[Signal]) -> list[Anomaly]:
        """Detect temporal inconsistencies."""
        anomalies = []
        
        # Check for retroactive edits (ingestion time vs source time)
        sorted_by_ingest = sorted(signals, key=lambda s: s.ingested_at)
        
        for i in range(len(sorted_by_ingest) - 1):
            curr = sorted_by_ingest[i]
            next_sig = sorted_by_ingest[i + 1]
            
            # If a later-ingested signal has an earlier source timestamp
            if curr.source_timestamp > next_sig.source_timestamp:
                time_diff = (curr.source_timestamp - next_sig.source_timestamp).days
                
                if time_diff > 7:  # More than a week is suspicious
                    anomalies.append(Anomaly(
                        anomaly_type="temporal",
                        severity="high",
                        description="Temporal inconsistency detected",
                        evidence=[
                            f"Signal ingested later has earlier source date",
                            f"Time discrepancy: {time_diff} days",
                            f"Sources: {curr.source}, {next_sig.source}",
                            "Possible retroactive data manipulation"
                        ],
                        confidence=0.8
                    ))
        
        # Check for missing expected signals (gaps in activity)
        if len(signals) >= 3:
            sorted_by_source = sorted(signals, key=lambda s: s.source_timestamp)
            
            for i in range(len(sorted_by_source) - 1):
                gap_days = (
                    sorted_by_source[i + 1].source_timestamp - 
                    sorted_by_source[i].source_timestamp
                ).days
                
                # Flag gaps >180 days (6 months of inactivity)
                if gap_days > 180:
                    anomalies.append(Anomaly(
                        anomaly_type="temporal",
                        severity="medium",
                        description="Extended period of inactivity",
                        evidence=[
                            f"{gap_days} days with no activity",
                            f"From {sorted_by_source[i].source_timestamp.date()} to {sorted_by_source[i+1].source_timestamp.date()}",
                            "May indicate abandoned project"
                        ],
                        confidence=0.7
                    ))
                    break  # Only report one gap
        
        return anomalies
    
    def detect_network_anomalies(
        self, founder_id: int, signals: list[Signal]
    ) -> list[Anomaly]:
        """Detect network-related anomalies."""
        anomalies = []
        
        # Check for isolated founder (no collaborations)
        github_signals = [s for s in signals if s.source == "github"]
        
        if github_signals:
            has_collaboration = False
            for sig in github_signals:
                if sig.record_type == "github_repo":
                    forks = sig.payload.get("forks", 0)
                    if forks > 0:
                        has_collaboration = True
                        break
            
            if not has_collaboration and len(github_signals) > 2:
                anomalies.append(Anomaly(
                    anomaly_type="network",
                    severity="medium",
                    description="No collaboration signals detected",
                    evidence=[
                        "No repository forks or contributors",
                        f"{len(github_signals)} GitHub signals, all solo work",
                        "May lack ecosystem connections"
                    ],
                    confidence=0.6
                ))
        
        # Check for suspicious engagement patterns
        # (Would analyze social media engagement, fake followers, etc. in production)
        
        return anomalies
    
    # Helper methods
    
    def _extract_metrics(self, signals: list[Signal]) -> dict[str, list[float]]:
        """Extract numeric metrics from signals."""
        metrics: dict[str, list[float]] = {
            "revenue": [],
            "users": [],
            "team_size": [],
            "github_stars": [],
        }
        
        for signal in signals:
            payload = signal.payload
            
            if "arr" in payload:
                metrics["revenue"].append(float(payload["arr"]))
            if "users" in payload:
                metrics["users"].append(float(payload["users"]))
            if "team_size" in payload:
                metrics["team_size"].append(float(payload["team_size"]))
            if signal.record_type == "github_profile" and "total_stars" in payload:
                metrics["github_stars"].append(float(payload["total_stars"]))
        
        # Remove empty metrics
        return {k: v for k, v in metrics.items() if v}
    
    def _check_too_good_to_be_true(
        self, metrics: dict[str, list[float]]
    ) -> list[Anomaly]:
        """Check for unrealistic claims."""
        anomalies = []
        
        # Check for extremely high growth rates
        for metric_name, values in metrics.items():
            if len(values) < 2:
                continue
            
            # Check growth rate
            growth = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
            
            # Flag if >10x growth in short period
            if growth > 10.0:
                anomalies.append(Anomaly(
                    anomaly_type="statistical",
                    severity="high",
                    description=f"Unusually high {metric_name} growth",
                    evidence=[
                        f"{growth:.1f}x growth ({values[0]:.0f} → {values[-1]:.0f})",
                        "Verify authenticity of claims",
                        "May be too good to be true"
                    ],
                    confidence=0.75
                ))
        
        return anomalies
    
    def _calculate_risk_level(self, anomalies: list[Anomaly]) -> str:
        """Calculate overall risk level from anomalies."""
        if not anomalies:
            return "low"
        
        critical_count = sum(1 for a in anomalies if a.severity == "critical")
        high_count = sum(1 for a in anomalies if a.severity == "high")
        medium_count = sum(1 for a in anomalies if a.severity == "medium")
        
        if critical_count > 0:
            return "critical"
        elif high_count >= 2:
            return "critical"
        elif high_count == 1:
            return "high"
        elif medium_count >= 3:
            return "high"
        elif medium_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _recommend_action(
        self, risk_level: str, anomalies: list[Anomaly]
    ) -> str:
        """Recommend action based on risk."""
        if risk_level == "critical":
            return "reject"
        elif risk_level == "high":
            return "flag"
        elif risk_level == "medium":
            return "investigate"
        else:
            return "proceed"
    
    def _empty_report(self, founder_id: int) -> AnomalyReport:
        """Return empty report when no data."""
        return AnomalyReport(
            founder_id=founder_id,
            statistical_anomalies=[],
            behavioral_anomalies=[],
            temporal_anomalies=[],
            network_anomalies=[],
            overall_risk_level="unknown",
            # Nothing has been examined yet, so there is nothing to investigate.
            # The honest instruction is to gather data, not to treat an empty
            # report as suspicious.
            recommended_action="gather_data",
            anomaly_count=0,
            generated_at=datetime.now(timezone.utc),
        )
