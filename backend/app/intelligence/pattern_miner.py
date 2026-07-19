"""Pattern mining engine for learning from historical decisions.

Identifies success patterns, failure modes, and optimizes investment thesis
based on past performance.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models.application import Application
from app.models.founder import Founder


@dataclass
class SuccessPattern:
    """A detected pattern associated with success."""
    pattern_name: str
    confidence: float  # 0-1
    support: int  # number of instances
    attributes: dict[str, Any]
    examples: list[int]  # founder_ids


@dataclass
class FailureMode:
    """A detected failure mode."""
    mode_name: str
    frequency: float  # 0-1 how often it leads to failure
    indicators: list[str]
    examples: list[int]


@dataclass
class ThesisOptimization:
    """Recommendations for thesis optimization."""
    current_performance: dict[str, float]
    recommended_changes: list[dict[str, Any]]
    expected_improvement: float
    reasoning: list[str]


@dataclass
class SuccessPatterns:
    """Complete pattern mining report."""
    high_confidence_rules: list[SuccessPattern]
    failure_modes: list[FailureMode]
    key_success_factors: list[tuple[str, float]]  # (factor, importance)
    thesis_optimization: ThesisOptimization
    analyzed_applications: int
    generated_at: datetime


class PatternMiningEngine:
    """Mines patterns from historical decisions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)
    
    def mine_success_patterns(
        self, 
        lookback_months: int = 24,
        min_confidence: float = 0.7
    ) -> SuccessPatterns:
        """Mine success patterns from historical data."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_months * 30)
        
        # Get historical applications
        historical = self.db.scalars(
            select(Application).where(Application.created_at >= cutoff)
        ).all()
        
        if not historical:
            return self._empty_patterns()
        
        # Label outcomes (would check actual funding/success in production)
        labeled = self._label_outcomes(historical)
        
        # Extract features for each application
        features = [self._extract_features(app) for app in labeled]
        
        # Mine association rules
        success_rules = self._mine_association_rules(
            features, 
            target='success',
            min_confidence=min_confidence
        )
        
        # Identify failure modes
        failure_modes = self._identify_failure_modes(features)
        
        # Rank features by importance
        key_factors = self._rank_features_by_importance(features)
        
        # Generate thesis optimization recommendations
        thesis_opt = self._optimize_thesis(features)
        
        return SuccessPatterns(
            high_confidence_rules=success_rules,
            failure_modes=failure_modes,
            key_success_factors=key_factors,
            thesis_optimization=thesis_opt,
            analyzed_applications=len(historical),
            generated_at=datetime.now(timezone.utc),
        )
    
    def _label_outcomes(self, applications: list[Application]) -> list[dict]:
        """Label applications with outcomes."""
        labeled = []
        
        for app in applications:
            # In production, would check:
            # - Did they get funded?
            # - Did they reach milestones?
            # - Exit/failure status
            
            # For now, use screening decision as proxy
            outcome = 'success' if app.screening_decision == 'pass' else 'failure'
            
            labeled.append({
                'application': app,
                'outcome': outcome,
                'founder_id': app.founder_id,
            })
        
        return labeled
    
    def _extract_features(self, labeled_app: dict) -> dict[str, Any]:
        """Extract features from an application."""
        app = labeled_app['application']
        outcome = labeled_app['outcome']
        
        founder = self.repo.get_founder(app.founder_id)
        company = self.repo.get_company(app.company_id)
        signals = self.repo.signals_for(app.founder_id)
        
        features = {
            'outcome': outcome,
            'founder_id': app.founder_id,
            'has_github': founder.github_handle is not None,
            'is_cold_start': founder.is_cold_start,
            'signal_count': len(signals),
            'channel': app.channel,
            'sector': company.sector if company else None,
            'stage': company.stage if company else None,
            'geography': company.geography if company else None,
        }
        
        # Extract metrics from signals
        for signal in signals:
            payload = signal.payload
            if 'arr' in payload:
                features['has_revenue'] = True
                features['revenue'] = float(payload['arr'])
            if 'users' in payload:
                features['has_users'] = True
                features['user_count'] = int(payload['users'])
            if signal.source == 'github':
                features['has_github_signal'] = True
        
        return features
    
    def _mine_association_rules(
        self,
        features: list[dict],
        target: str,
        min_confidence: float
    ) -> list[SuccessPattern]:
        """Mine association rules (simple frequency-based)."""
        rules = []
        
        # Filter successful cases
        successful = [f for f in features if f.get('outcome') == target]
        total_success = len(successful)
        
        if total_success < 5:  # Need minimum sample
            return rules
        
        # Check common patterns in successful cases
        patterns_to_check = [
            ('has_github', 'Has GitHub presence'),
            ('has_revenue', 'Has revenue'),
            ('has_users', 'Has user traction'),
            ('channel', 'Source channel'),
        ]
        
        for feature_key, pattern_name in patterns_to_check:
            if feature_key not in successful[0]:
                continue
            
            # Count frequency in successful cases
            feature_values = [f.get(feature_key) for f in successful if f.get(feature_key)]
            
            if not feature_values:
                continue
            
            # For boolean features
            if isinstance(feature_values[0], bool):
                true_count = sum(1 for v in feature_values if v)
                confidence = true_count / len(feature_values)
                
                if confidence >= min_confidence:
                    rules.append(SuccessPattern(
                        pattern_name=f"{pattern_name} = True",
                        confidence=confidence,
                        support=true_count,
                        attributes={feature_key: True},
                        examples=[
                            f['founder_id'] 
                            for f in successful 
                            if f.get(feature_key) == True
                        ][:5]
                    ))
            
            # For categorical features
            elif isinstance(feature_values[0], str):
                value_counts = Counter(feature_values)
                most_common = value_counts.most_common(3)
                
                for value, count in most_common:
                    confidence = count / len(feature_values)
                    if confidence >= min_confidence:
                        rules.append(SuccessPattern(
                            pattern_name=f"{pattern_name} = {value}",
                            confidence=confidence,
                            support=count,
                            attributes={feature_key: value},
                            examples=[
                                f['founder_id']
                                for f in successful
                                if f.get(feature_key) == value
                            ][:5]
                        ))
        
        # Sort by confidence
        rules.sort(key=lambda x: x.confidence, reverse=True)
        
        return rules[:10]  # Top 10
    
    def _identify_failure_modes(self, features: list[dict]) -> list[FailureMode]:
        """Identify common failure patterns."""
        failures = [f for f in features if f.get('outcome') == 'failure']
        
        if len(failures) < 3:
            return []
        
        modes = []
        
        # Check for common failure indicators
        no_signals = sum(1 for f in failures if f.get('signal_count', 0) < 3)
        if no_signals > len(failures) * 0.5:
            modes.append(FailureMode(
                mode_name="Insufficient Data",
                frequency=no_signals / len(failures),
                indicators=["Less than 3 signals", "Limited founder information"],
                examples=[f['founder_id'] for f in failures if f.get('signal_count', 0) < 3][:5]
            ))
        
        # Cold start failures
        cold_start_fails = sum(1 for f in failures if f.get('is_cold_start'))
        if cold_start_fails > len(failures) * 0.3:
            modes.append(FailureMode(
                mode_name="Cold Start Risk",
                frequency=cold_start_fails / len(failures),
                indicators=["Cold start founder", "No track record"],
                examples=[f['founder_id'] for f in failures if f.get('is_cold_start')][:5]
            ))
        
        # No revenue
        no_revenue = sum(1 for f in failures if not f.get('has_revenue'))
        if no_revenue > len(failures) * 0.6:
            modes.append(FailureMode(
                mode_name="No Revenue",
                frequency=no_revenue / len(failures),
                indicators=["No revenue signals", "Pre-revenue stage"],
                examples=[f['founder_id'] for f in failures if not f.get('has_revenue')][:5]
            ))
        
        return modes
    
    def _rank_features_by_importance(
        self, features: list[dict]
    ) -> list[tuple[str, float]]:
        """Rank features by their correlation with success."""
        if not features:
            return []
        
        successful = [f for f in features if f.get('outcome') == 'success']
        failed = [f for f in features if f.get('outcome') == 'failure']
        
        if not successful or not failed:
            return []
        
        importance = []
        
        feature_keys = ['has_github', 'has_revenue', 'has_users', 'signal_count']
        
        for key in feature_keys:
            # Calculate success rate when feature is present/high
            if key in successful[0]:
                if isinstance(successful[0][key], bool):
                    success_with = sum(1 for f in successful if f.get(key)) / len(successful)
                    fail_with = sum(1 for f in failed if f.get(key)) / len(failed)
                    diff = success_with - fail_with
                    if diff > 0:
                        importance.append((key, diff))
                elif isinstance(successful[0][key], (int, float)):
                    success_avg = sum(f.get(key, 0) for f in successful) / len(successful)
                    fail_avg = sum(f.get(key, 0) for f in failed) / len(failed)
                    if success_avg > fail_avg:
                        normalized_diff = min(1.0, (success_avg - fail_avg) / (success_avg + 1))
                        importance.append((key, normalized_diff))
        
        importance.sort(key=lambda x: x[1], reverse=True)
        
        return importance[:10]
    
    def _optimize_thesis(self, features: list[dict]) -> ThesisOptimization:
        """Generate thesis optimization recommendations."""
        if not features:
            return ThesisOptimization(
                current_performance={},
                recommended_changes=[],
                expected_improvement=0.0,
                reasoning=["Insufficient data"]
            )
        
        # Calculate current performance
        successful = [f for f in features if f.get('outcome') == 'success']
        success_rate = len(successful) / len(features) if features else 0.0
        
        # Analyze by sector
        sector_performance = defaultdict(lambda: {'success': 0, 'total': 0})
        for f in features:
            sector = f.get('sector', 'Unknown')
            sector_performance[sector]['total'] += 1
            if f.get('outcome') == 'success':
                sector_performance[sector]['success'] += 1
        
        # Find best performing sectors
        sector_rates = {
            sector: stats['success'] / stats['total']
            for sector, stats in sector_performance.items()
            if stats['total'] >= 3  # Minimum sample
        }
        
        recommendations = []
        reasoning = []
        
        if sector_rates:
            best_sectors = sorted(sector_rates.items(), key=lambda x: x[1], reverse=True)[:3]
            worst_sectors = sorted(sector_rates.items(), key=lambda x: x[1])[:2]
            
            if best_sectors[0][1] > success_rate * 1.2:
                recommendations.append({
                    'type': 'focus_sectors',
                    'sectors': [s[0] for s in best_sectors],
                    'expected_improvement': best_sectors[0][1] - success_rate
                })
                reasoning.append(
                    f"Focus on {', '.join(s[0] for s in best_sectors[:2])} "
                    f"(success rate: {best_sectors[0][1]:.0%})"
                )
            
            if worst_sectors and worst_sectors[0][1] < success_rate * 0.5:
                recommendations.append({
                    'type': 'avoid_sectors',
                    'sectors': [s[0] for s in worst_sectors]
                })
                reasoning.append(
                    f"Avoid {worst_sectors[0][0]} (low success rate: {worst_sectors[0][1]:.0%})"
                )
        
        # Check channel performance
        channel_performance = defaultdict(lambda: {'success': 0, 'total': 0})
        for f in features:
            channel = f.get('channel', 'unknown')
            channel_performance[channel]['total'] += 1
            if f.get('outcome') == 'success':
                channel_performance[channel]['success'] += 1
        
        channel_rates = {
            ch: stats['success'] / stats['total']
            for ch, stats in channel_performance.items()
            if stats['total'] >= 2
        }
        
        if channel_rates:
            best_channel = max(channel_rates.items(), key=lambda x: x[1])
            if best_channel[1] > success_rate * 1.3:
                recommendations.append({
                    'type': 'prioritize_channel',
                    'channel': best_channel[0],
                    'current_rate': best_channel[1]
                })
                reasoning.append(
                    f"Prioritize {best_channel[0]} channel (success rate: {best_channel[1]:.0%})"
                )
        
        expected_improvement = 0.0
        if recommendations:
            # Estimate improvement (weighted avg of recommended changes)
            improvements = [r.get('expected_improvement', 0.1) for r in recommendations]
            expected_improvement = sum(improvements) / len(improvements)
        
        return ThesisOptimization(
            current_performance={
                'success_rate': success_rate,
                'total_applications': len(features),
                'successful_applications': len(successful),
            },
            recommended_changes=recommendations,
            expected_improvement=expected_improvement,
            reasoning=reasoning if reasoning else ["Current thesis performing adequately"]
        )
    
    def _empty_patterns(self) -> SuccessPatterns:
        """Return empty patterns when no data."""
        return SuccessPatterns(
            high_confidence_rules=[],
            failure_modes=[],
            key_success_factors=[],
            thesis_optimization=ThesisOptimization(
                current_performance={},
                recommended_changes=[],
                expected_improvement=0.0,
                reasoning=["No historical data available"]
            ),
            analyzed_applications=0,
            generated_at=datetime.now(timezone.utc),
        )
