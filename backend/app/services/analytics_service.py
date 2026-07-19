"""Advanced analytics service for dashboard insights.

Provides aggregated analytics, trends, and intelligence summaries
for the investor dashboard.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.intelligence.pattern_miner import PatternMiningEngine
from app.intelligence.signal_analyzer import SignalCorrelationEngine
from app.memory.repository import MemoryRepository
from app.models.application import Application
from app.models.founder import Founder
from app.models.signal import Signal


@dataclass
class PipelineMetrics:
    """Pipeline health metrics."""
    total_founders: int
    total_applications: int
    by_stage: dict[str, int]
    by_channel: dict[str, int]
    screening_pass_rate: float
    avg_signals_per_founder: float


@dataclass
class MomentumTrends:
    """Momentum trends across portfolio."""
    founders_with_positive_momentum: int
    founders_with_negative_momentum: int
    hot_sectors: list[tuple[str, int]]
    emerging_geographies: list[tuple[str, int]]


@dataclass
class QualityMetrics:
    """Data quality metrics."""
    avg_signal_quality: float
    high_quality_founders: int
    founders_needing_more_data: int
    contradiction_rate: float


@dataclass
class DashboardAnalytics:
    """Complete dashboard analytics."""
    pipeline_metrics: PipelineMetrics
    momentum_trends: MomentumTrends
    quality_metrics: QualityMetrics
    top_opportunities: list[dict]
    recent_activity: list[dict]
    actionable_insights: list[str]
    generated_at: datetime


class AnalyticsService:
    """Advanced analytics for dashboard."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)
    
    def get_dashboard_analytics(self, lookback_days: int = 30) -> DashboardAnalytics:
        """Get comprehensive dashboard analytics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        # Calculate all metrics
        pipeline = self._calculate_pipeline_metrics(cutoff)
        momentum = self._analyze_momentum_trends(cutoff)
        quality = self._assess_data_quality()
        top_opps = self._identify_top_opportunities()
        recent = self._get_recent_activity(limit=10)
        insights = self._generate_actionable_insights(
            pipeline, momentum, quality
        )
        
        return DashboardAnalytics(
            pipeline_metrics=pipeline,
            momentum_trends=momentum,
            quality_metrics=quality,
            top_opportunities=top_opps,
            recent_activity=recent,
            actionable_insights=insights,
            generated_at=datetime.now(timezone.utc),
        )
    
    def _calculate_pipeline_metrics(self, cutoff: datetime) -> PipelineMetrics:
        """Calculate pipeline health metrics."""
        # Total founders
        total_founders = self.db.scalar(select(func.count(Founder.id)))
        
        # Total applications
        total_apps = self.db.scalar(select(func.count(Application.id)))
        
        # By screening stage
        by_stage = defaultdict(int)
        apps = self.db.scalars(select(Application)).all()
        for app in apps:
            stage = app.screening_decision or "pending"
            by_stage[stage] += 1
        
        # By channel
        by_channel = defaultdict(int)
        for app in apps:
            by_channel[app.channel] += 1
        
        # Pass rate
        passed = by_stage.get("pass", 0)
        total = sum(by_stage.values())
        pass_rate = passed / total if total > 0 else 0.0
        
        # Signals per founder
        total_signals = self.db.scalar(select(func.count(Signal.id)))
        avg_signals = total_signals / total_founders if total_founders > 0 else 0.0
        
        return PipelineMetrics(
            total_founders=total_founders or 0,
            total_applications=total_apps or 0,
            by_stage=dict(by_stage),
            by_channel=dict(by_channel),
            screening_pass_rate=pass_rate,
            avg_signals_per_founder=avg_signals,
        )
    
    def _analyze_momentum_trends(self, cutoff: datetime) -> MomentumTrends:
        """Analyze momentum across the portfolio."""
        analyzer = SignalCorrelationEngine(self.db)
        
        positive_momentum = 0
        negative_momentum = 0
        sector_counts = defaultdict(int)
        geo_counts = defaultdict(int)
        
        founders = self.db.scalars(select(Founder)).all()
        
        for founder in founders:
            signals = self.repo.signals_for(founder.id)
            if not signals:
                continue
            
            try:
                # Analyze momentum
                report = analyzer.analyze_founder_signals(founder.id)
                
                # Count momentum directions
                accelerating = [
                    m for m in report.momentum_indicators 
                    if m.direction == "accelerating"
                ]
                declining = [
                    m for m in report.momentum_indicators 
                    if m.direction in ("decelerating", "declining")
                ]
                
                if accelerating and len(accelerating) > len(declining):
                    positive_momentum += 1
                elif declining and len(declining) > len(accelerating):
                    negative_momentum += 1
                
                # Track sectors and geographies
                apps = self.db.scalars(
                    select(Application).where(Application.founder_id == founder.id)
                ).all()
                
                for app in apps:
                    company = self.repo.get_company(app.company_id)
                    if company:
                        if company.sector:
                            sector_counts[company.sector] += 1
                        if company.geography:
                            geo_counts[company.geography] += 1
            except:
                continue
        
        # Top sectors and geos
        hot_sectors = sorted(
            sector_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        emerging_geos = sorted(
            geo_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return MomentumTrends(
            founders_with_positive_momentum=positive_momentum,
            founders_with_negative_momentum=negative_momentum,
            hot_sectors=hot_sectors,
            emerging_geographies=emerging_geos,
        )
    
    def _assess_data_quality(self) -> QualityMetrics:
        """Assess overall data quality."""
        analyzer = SignalCorrelationEngine(self.db)
        
        quality_scores = []
        high_quality = 0
        needs_data = 0
        contradictions = 0
        total_analyzed = 0
        
        founders = self.db.scalars(select(Founder).limit(100)).all()
        
        for founder in founders:
            signals = self.repo.signals_for(founder.id)
            
            if len(signals) < 3:
                needs_data += 1
                continue
            
            try:
                report = analyzer.analyze_founder_signals(founder.id)
                total_analyzed += 1
                
                # Calculate quality score
                quality = (
                    report.consistency_score * 0.5 +
                    report.confidence * 0.5
                )
                quality_scores.append(quality)
                
                if quality > 0.7:
                    high_quality += 1
                
                if report.contradictions:
                    contradictions += 1
            except:
                continue
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        contradiction_rate = contradictions / total_analyzed if total_analyzed > 0 else 0.0
        
        return QualityMetrics(
            avg_signal_quality=avg_quality,
            high_quality_founders=high_quality,
            founders_needing_more_data=needs_data,
            contradiction_rate=contradiction_rate,
        )
    
    def _identify_top_opportunities(self, limit: int = 10) -> list[dict]:
        """Identify top investment opportunities."""
        opportunities = []
        
        # Get all applications
        apps = self.db.scalars(
            select(Application).where(Application.screening_decision == "pass")
        ).all()
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for app in apps:
            founder = self.repo.get_founder(app.founder_id)
            company = self.repo.get_company(app.company_id)
            signals = self.repo.signals_for(app.founder_id)
            
            # Score opportunity
            score = 0.5  # Base score
            
            # More signals = higher confidence
            score += min(0.2, len(signals) / 50)
            
            # Recent activity
            recent = []
            for s in signals:
                ts = s.source_timestamp
                # Make timezone-aware if needed
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if (now - ts).days <= 90:
                    recent.append(s)
            
            if recent:
                score += 0.15
            
            # GitHub presence
            if founder.github_handle:
                score += 0.15
            
            opportunities.append({
                "founder_id": founder.id,
                "founder_name": founder.name,
                "company_name": company.name if company else None,
                "sector": company.sector if company else None,
                "score": score,
                "signal_count": len(signals),
                "channel": app.channel,
            })
        
        # Sort by score
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        
        return opportunities[:limit]
    
    def _get_recent_activity(self, limit: int = 10) -> list[dict]:
        """Get recent activity feed."""
        activity = []
        
        # Recent applications
        recent_apps = self.db.scalars(
            select(Application)
            .order_by(Application.created_at.desc())
            .limit(limit)
        ).all()
        
        for app in recent_apps:
            founder = self.repo.get_founder(app.founder_id)
            company = self.repo.get_company(app.company_id)
            
            activity.append({
                "type": "application",
                "timestamp": app.created_at.isoformat(),
                "description": f"New {app.channel} application: {founder.name} - {company.name if company else 'Unknown'}",
                "founder_id": founder.id,
            })
        
        # Recent signals (top sources)
        recent_signals = self.db.scalars(
            select(Signal)
            .order_by(Signal.ingested_at.desc())
            .limit(limit)
        ).all()
        
        for signal in recent_signals:
            if signal.founder_id:
                founder = self.repo.get_founder(signal.founder_id)
                activity.append({
                    "type": "signal",
                    "timestamp": signal.ingested_at.isoformat(),
                    "description": f"New {signal.source} signal for {founder.name if founder else 'Unknown'}",
                    "founder_id": signal.founder_id,
                })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return activity[:limit]
    
    def _generate_actionable_insights(
        self,
        pipeline: PipelineMetrics,
        momentum: MomentumTrends,
        quality: QualityMetrics
    ) -> list[str]:
        """Generate actionable insights."""
        insights = []
        
        # Pipeline insights
        if pipeline.screening_pass_rate < 0.3:
            insights.append(
                f"⚠️ Low screening pass rate ({pipeline.screening_pass_rate:.0%}). "
                "Review screening criteria or improve sourcing quality."
            )
        
        if pipeline.avg_signals_per_founder < 5:
            insights.append(
                f"📊 Average {pipeline.avg_signals_per_founder:.1f} signals per founder. "
                "Consider running more scans to enrich data."
            )
        
        # Momentum insights
        if momentum.founders_with_positive_momentum > momentum.founders_with_negative_momentum * 2:
            insights.append(
                f"🚀 Strong momentum: {momentum.founders_with_positive_momentum} founders accelerating. "
                "Good time to review top opportunities."
            )
        elif momentum.founders_with_negative_momentum > momentum.founders_with_positive_momentum:
            insights.append(
                f"⚡ {momentum.founders_with_negative_momentum} founders showing declining momentum. "
                "Check in on portfolio companies."
            )
        
        # Sector insights
        if momentum.hot_sectors:
            top_sector = momentum.hot_sectors[0]
            insights.append(
                f"🔥 Hot sector: {top_sector[0]} ({top_sector[1]} founders). "
                "Consider increasing allocation."
            )
        
        # Quality insights
        if quality.contradiction_rate > 0.2:
            insights.append(
                f"⚠️ {quality.contradiction_rate:.0%} of founders have data contradictions. "
                "Run validation checks before decisions."
            )
        
        if quality.founders_needing_more_data > 10:
            insights.append(
                f"📋 {quality.founders_needing_more_data} founders need more data. "
                "Run additional scans for better assessment."
            )
        
        # Default positive message if no concerns
        if not insights:
            insights.append("✅ Pipeline healthy. All metrics within normal ranges.")
        
        return insights
