"""Sourcing service — outbound discovery + activation (FR-5, Epic D).

Activation (D3) is the step that turns a passive watchlist into a real pipeline:
a discovered founder (scanned from GitHub/arXiv/etc., no application yet) is
converted into an Application on the OUTBOUND channel and dropped into the exact
same screening funnel as inbound applicants — channel is recorded for analytics
but never fed to any scorer (D2 consistency guarantee).

Enhanced with intelligent scoring and channel analytics.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence.screening import first_pass
from app.intelligence.signal_analyzer import SignalCorrelationEngine
from app.memory.repository import MemoryRepository
from app.models.application import Application
from app.models.founder import Founder
from app.models.outreach import Outreach
from app.models.signal import Signal


@dataclass
class DiscoveredFounderInfo:
    """Enhanced discovered founder information."""
    founder_id: int
    name: str
    github_handle: str | None
    is_cold_start: bool
    founder_score: float | None
    momentum: str | None
    signal_count: int
    # New intelligence fields
    quality_score: float
    red_flags: list[str]
    green_flags: list[str]
    activation_recommendation: str  # auto_activate, review, skip
    activation_priority: float  # 0-1


def discovered_founders(db: Session, include_intelligence: bool = True) -> list[dict]:
    """
    Founders in Memory with no application yet — the outbound watchlist.
    
    Args:
        db: Database session
        include_intelligence: If True, run signal analysis for each founder
    
    Returns:
        List of discovered founders with intelligence scores
    """
    repo = MemoryRepository(db)
    analyzer = SignalCorrelationEngine(db) if include_intelligence else None
    
    # Get founders without applications
    with_apps = select(Application.founder_id)
    founders = db.scalars(
        select(Founder).where(~Founder.id.in_(with_apps)).order_by(Founder.created_at.desc())
    )
    
    rows = []
    for f in founders:
        latest = repo.latest_score(f.id)
        signal_count = len(repo.signals_for(f.id))
        
        # Base info
        info = {
            "founder_id": f.id,
            "name": f.name,
            "github_handle": f.github_handle,
            "is_cold_start": f.is_cold_start,
            "founder_score": latest.value if latest else None,
            "momentum": latest.momentum if latest else None,
            "signal_count": signal_count,
        }
        
        # Add intelligence analysis if requested
        if include_intelligence and signal_count > 0:
            try:
                analysis = analyzer.analyze_founder_signals(f.id)
                
                # Calculate quality score (0-1)
                quality = (
                    analysis.consistency_score * 0.4 +
                    analysis.confidence * 0.3 +
                    (1.0 - min(1.0, len(analysis.contradictions) * 0.2)) * 0.3
                )
                
                # Determine activation recommendation
                if quality > 0.7 and not analysis.red_flags:
                    recommendation = "auto_activate"
                    priority = 0.9
                elif quality > 0.5 and len(analysis.red_flags) <= 1:
                    recommendation = "review"
                    priority = 0.6
                else:
                    recommendation = "skip"
                    priority = 0.3
                
                info.update({
                    "quality_score": quality,
                    "red_flags": analysis.red_flags[:3],  # Top 3
                    "green_flags": analysis.green_flags[:3],
                    "activation_recommendation": recommendation,
                    "activation_priority": priority,
                })
            except Exception as e:
                # If analysis fails, include error but don't break the list
                info.update({
                    "quality_score": 0.0,
                    "red_flags": [f"Analysis error: {str(e)}"],
                    "green_flags": [],
                    "activation_recommendation": "review",
                    "activation_priority": 0.5,
                })
        else:
            # No signals or analysis not requested
            info.update({
                "quality_score": 0.0,
                "red_flags": ["Insufficient signals"] if signal_count == 0 else [],
                "green_flags": [],
                "activation_recommendation": "skip" if signal_count == 0 else "review",
                "activation_priority": 0.2 if signal_count == 0 else 0.5,
            })
        
        rows.append(info)
    
    # Sort by activation priority (highest first)
    rows.sort(key=lambda x: x.get("activation_priority", 0), reverse=True)
    
    return rows


def activate_founder(founder_id: int, company: dict, db: Session) -> dict:
    """Convert a discovered founder into a real application (outbound channel).

    Records the outreach as activated, creates the opportunity, and immediately
    runs the same first-pass screening inbound applications get.
    """
    repo = MemoryRepository(db)
    founder = repo.get_founder(founder_id)
    if founder is None:
        raise ValueError(f"Founder {founder_id} not found")

    comp = repo.create_company(company)
    application = repo.create_application(founder_id, comp.id, channel="outbound")
    db.add(Outreach(founder_id=founder_id, channel="email", status="activated"))
    db.commit()

    screening = first_pass(application.id, db)
    
    # Run signal analysis for activation report
    analyzer = SignalCorrelationEngine(db)
    try:
        analysis = analyzer.analyze_founder_signals(founder_id)
        intelligence_report = {
            "consistency_score": analysis.consistency_score,
            "confidence": analysis.confidence,
            "red_flags": analysis.red_flags,
            "green_flags": analysis.green_flags,
            "contradictions_count": len(analysis.contradictions),
        }
    except Exception:
        intelligence_report = None
    
    # Draft the cold-outreach message that would accompany this activation —
    # grounded in the founder's observed signals ("we noticed your work"),
    # never blocking: a failed draft returns None.
    from app.services.outreach_service import draft_outreach

    return {
        "application_id": application.id,
        "founder_id": founder_id,
        "founder_name": founder.name,
        "company_name": comp.name,
        "channel": "outbound",
        "screening": {
            "decision": screening.decision,
            "reason": screening.reason,
            "thesis_fit": screening.thesis_fit,
        },
        "intelligence": intelligence_report,
        "outreach_draft": draft_outreach(founder_id, db),
    }


def channel_performance_analytics(db: Session, lookback_days: int = 180) -> dict:
    """
    Analyze which sourcing channels produce the best founders.
    
    Returns detailed channel analytics in the format expected by frontend:
    - by_channel: Performance breakdown by inbound/outbound
    - by_source: Discovery source breakdown (GitHub, ProductHunt, etc.)
    - underexplored: Sources to prioritize
    - suggestion: Actionable recommendation
    """
    from datetime import datetime, timedelta, timezone
    from collections import Counter
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    
    # Get all applications since cutoff
    all_apps = db.scalars(
        select(Application).where(Application.created_at >= cutoff)
    ).all()
    
    if not all_apps:
        return {
            "by_channel": [],
            "by_source": [],
            "underexplored": ["github", "producthunt", "linkedin"],
            "suggestion": "Start by scanning GitHub profiles to build your initial pipeline."
        }
    
    # Group by channel (inbound vs outbound)
    by_channel = defaultdict(lambda: {
        "count": 0,
        "scores": [],
        "thesis_fits": [],
        "passes": 0
    })
    
    for app in all_apps:
        channel = app.channel or "unknown"
        by_channel[channel]["count"] += 1
        
        # Collect scores from axis_scores
        if app.scores:
            # Calculate founder score (average of non-thesis axes)
            non_thesis_scores = [s.value for s in app.scores if s.axis != "thesis_fit"]
            if non_thesis_scores:
                founder_score = sum(non_thesis_scores) / len(non_thesis_scores)
                by_channel[channel]["scores"].append(founder_score)
            
            # Get thesis fit score
            thesis_scores = [s.value for s in app.scores if s.axis == "thesis_fit"]
            if thesis_scores:
                by_channel[channel]["thesis_fits"].append(thesis_scores[0])
        
        if app.screening_decision == "pass":
            by_channel[channel]["passes"] += 1
    
    # Format channel stats
    channel_stats = []
    for channel, data in by_channel.items():
        avg_founder = sum(data["scores"]) / len(data["scores"]) if data["scores"] else None
        avg_thesis = sum(data["thesis_fits"]) / len(data["thesis_fits"]) if data["thesis_fits"] else None
        pass_rate = data["passes"] / data["count"] if data["count"] > 0 else 0.0
        
        channel_stats.append({
            "channel": channel,
            "count": data["count"],
            "avg_founder_score": round(avg_founder, 1) if avg_founder else None,
            "avg_thesis_fit": round(avg_thesis, 1) if avg_thesis else None,
            "pass_rate": pass_rate,
            "avg_axes": {}  # Could add axis breakdown here
        })
    
    # Get signal sources
    source_counter = Counter()
    for app in all_apps:
        # Get signals for this founder
        signals = db.scalars(
            select(Signal).where(Signal.founder_id == app.founder_id)
        ).all()
        
        for signal in signals:
            source_counter[signal.source] += 1
    
    by_source = [
        {"source": source, "founders": count}
        for source, count in source_counter.most_common()
    ]
    
    # Identify underexplored sources
    all_possible_sources = ["github", "linkedin", "producthunt", "angellist", "twitter", "ycombinator"]
    used_sources = set(source_counter.keys())
    underexplored = [s for s in all_possible_sources if s not in used_sources or source_counter[s] < 3]
    
    # Generate suggestion
    suggestion = None
    if channel_stats:
        # Find best performing channel
        best_channel = max(channel_stats, key=lambda x: x.get("avg_founder_score") or 0)
        worst_channel = min(channel_stats, key=lambda x: x.get("avg_founder_score") or 0)
        
        if best_channel["avg_founder_score"] and worst_channel["avg_founder_score"]:
            if best_channel["avg_founder_score"] > worst_channel["avg_founder_score"] + 10:
                suggestion = f"{best_channel['channel'].capitalize()} is outperforming {worst_channel['channel']} by {best_channel['avg_founder_score'] - worst_channel['avg_founder_score']:.0f} points. Consider allocating more resources to {best_channel['channel']}."
            elif best_channel["pass_rate"] > 0.7:
                suggestion = f"{best_channel['channel'].capitalize()} has a strong {best_channel['pass_rate']*100:.0f}% pass rate. This channel is working well."
            elif underexplored:
                suggestion = f"Try exploring {underexplored[0].title()} to diversify your sourcing channels."
    
    if not suggestion and underexplored:
        suggestion = f"Consider scanning {underexplored[0].title()} to find more founders. This source is underutilized."
    
    return {
        "by_channel": channel_stats,
        "by_source": by_source,
        "underexplored": underexplored[:3],  # Top 3
        "suggestion": suggestion
    }
