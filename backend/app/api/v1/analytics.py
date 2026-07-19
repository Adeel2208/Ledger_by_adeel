"""Analytics and insights endpoints for dashboard intelligence."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import AnalyticsService


router = APIRouter()


class AnalyticsRequest(BaseModel):
    lookback_days: int = Field(default=30, ge=1, le=365, description="Days of data to analyze")


@router.get("/dashboard")
def get_dashboard_analytics(
    lookback_days: int = 30,
    db: Session = Depends(get_db)
) -> dict:
    """
    Comprehensive dashboard analytics.
    
    Returns:
    - Pipeline metrics (funnel, conversion rates)
    - Momentum trends (positive/negative, hot sectors)
    - Quality metrics (data completeness, contradictions)
    - Top opportunities
    - Recent activity
    - Actionable insights
    """
    service = AnalyticsService(db)
    analytics = service.get_dashboard_analytics(lookback_days=lookback_days)
    
    return {
        "pipeline_metrics": {
            "total_founders": analytics.pipeline_metrics.total_founders,
            "total_applications": analytics.pipeline_metrics.total_applications,
            "by_stage": analytics.pipeline_metrics.by_stage,
            "by_channel": analytics.pipeline_metrics.by_channel,
            "screening_pass_rate": analytics.pipeline_metrics.screening_pass_rate,
            "avg_signals_per_founder": analytics.pipeline_metrics.avg_signals_per_founder,
        },
        "momentum_trends": {
            "founders_with_positive_momentum": analytics.momentum_trends.founders_with_positive_momentum,
            "founders_with_negative_momentum": analytics.momentum_trends.founders_with_negative_momentum,
            "hot_sectors": [
                {"sector": sector, "count": count}
                for sector, count in analytics.momentum_trends.hot_sectors
            ],
            "emerging_geographies": [
                {"geography": geo, "count": count}
                for geo, count in analytics.momentum_trends.emerging_geographies
            ],
        },
        "quality_metrics": {
            "avg_signal_quality": analytics.quality_metrics.avg_signal_quality,
            "high_quality_founders": analytics.quality_metrics.high_quality_founders,
            "founders_needing_more_data": analytics.quality_metrics.founders_needing_more_data,
            "contradiction_rate": analytics.quality_metrics.contradiction_rate,
        },
        "top_opportunities": analytics.top_opportunities,
        "recent_activity": analytics.recent_activity,
        "actionable_insights": analytics.actionable_insights,
        "generated_at": analytics.generated_at.isoformat(),
    }


@router.get("/channels")
def channel_performance_legacy(db: Session = Depends(get_db)) -> dict:
    """Legacy channel performance endpoint - use /sourcing/channel-analytics instead."""
    from app.services.sourcing_service import channel_performance_analytics
    return channel_performance_analytics(db)
