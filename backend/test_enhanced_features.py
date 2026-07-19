"""
Integration tests for enhanced search and analysis features.

Run with: python -m pytest test_enhanced_features.py -v
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.intelligence.anomaly_detector import AnomalyDetector
from app.intelligence.predictive import PredictiveEngine
from app.intelligence.reasoning import parse_query, resolve_query
from app.intelligence.retrieval import BM25Index, HybridIndex, reciprocal_rank_fusion
from app.intelligence.signal_analyzer import SignalCorrelationEngine
from app.memory.ingestion.base import Confidence, RawSignal
from app.memory.repository import MemoryRepository
from app.models.founder import Founder
from app.models.signal import Signal


@pytest.fixture
def db_session():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_founder(db_session: Session):
    """Create a sample founder with signals."""
    repo = MemoryRepository(db_session)
    
    # Create founder
    founder = repo.create_founder({
        "name": "Jane Doe",
        "email": "jane@example.com",
        "github_handle": "janedoe"
    })
    
    # Add various signals
    now = datetime.now(timezone.utc)
    
    signals = [
        RawSignal(
            source="github",
            record_type="github_profile",
            payload={
                "total_stars": 500,
                "followers": 100,
                "public_repos": 10
            },
            timestamp=now - timedelta(days=30),
            confidence=Confidence.VERIFIED
        ),
        RawSignal(
            source="github",
            record_type="github_profile",
            payload={
                "total_stars": 750,
                "followers": 150,
                "public_repos": 12
            },
            timestamp=now,
            confidence=Confidence.VERIFIED
        ),
        RawSignal(
            source="deck",
            record_type="traction_claim",
            payload={
                "arr": 500_000,
                "users": 5000,
                "team_size": 5
            },
            timestamp=now - timedelta(days=10),
            confidence=Confidence.CLAIMED
        ),
        RawSignal(
            source="web",
            record_type="public_footprint",
            payload={
                "users": 5100,  # Consistent with deck
                "description": "AI-powered developer tools"
            },
            timestamp=now - timedelta(days=5),
            confidence=Confidence.SCRAPED
        ),
    ]
    
    for raw_signal in signals:
        repo.add_signal(founder.id, raw_signal)
    
    db_session.commit()
    
    return founder


class TestNaturalLanguageQueryParsing:
    """Test the NL query parser."""
    
    def test_parse_simple_query(self):
        """Test parsing a simple query."""
        query = "technical founder in Berlin working on AI"
        parsed = parse_query(query)
        
        assert parsed is not None
        assert isinstance(parsed.semantic_query, str)
        assert len(parsed.semantic_query) > 0
    
    def test_parse_complex_query(self):
        """Test parsing a complex query with multiple constraints."""
        query = "serial entrepreneur, no prior VC, raised <$2M, growing >20% MoM"
        parsed = parse_query(query)
        
        assert parsed is not None
        # Should extract serial entrepreneur attribute
        # Should detect no_vc_backing negation
        # Should parse funding range


class TestHybridSearch:
    """Test hybrid BM25 + dense search."""
    
    def test_bm25_index(self):
        """Test BM25 indexing and search."""
        index = BM25Index()
        
        # Index documents
        docs = [
            "technical founder building AI infrastructure",
            "serial entrepreneur with successful exit",
            "YC alum working on developer tools"
        ]
        ids = ["doc1", "doc2", "doc3"]
        metadata = [{"source": "test"} for _ in docs]
        
        index.upsert(ids, docs, metadata)
        
        # Search
        results = index.search("technical AI", k=2)
        
        assert len(results) > 0
        assert results[0]["id"] == "doc1"  # Should rank highest
    
    def test_reciprocal_rank_fusion(self):
        """Test RRF merging."""
        results1 = [
            {"id": "doc1", "score": 0.9, "metadata": {}},
            {"id": "doc2", "score": 0.7, "metadata": {}},
        ]
        results2 = [
            {"id": "doc2", "score": 0.8, "metadata": {}},
            {"id": "doc3", "score": 0.6, "metadata": {}},
        ]
        
        fused = reciprocal_rank_fusion([results1, results2])
        
        assert len(fused) == 3
        # doc2 appears in both, should rank high
        doc_ids = [r["id"] for r in fused]
        assert "doc2" in doc_ids


class TestSignalCorrelation:
    """Test signal correlation engine."""
    
    def test_analyze_founder_signals(self, db_session: Session, sample_founder: Founder):
        """Test complete signal analysis."""
        engine = SignalCorrelationEngine(db_session)
        
        report = engine.analyze_founder_signals(sample_founder.id)
        
        assert report is not None
        assert report.founder_id == sample_founder.id
        assert report.consistency_score >= 0.0
        assert report.consistency_score <= 1.0
        assert isinstance(report.contradictions, list)
        assert isinstance(report.momentum_indicators, list)
        assert isinstance(report.quality_signals, list)
    
    def test_detect_momentum(self, db_session: Session, sample_founder: Founder):
        """Test momentum detection."""
        engine = SignalCorrelationEngine(db_session)
        signals = engine.repo.signals_for(sample_founder.id)
        
        momentum = engine.detect_momentum(signals)
        
        assert isinstance(momentum, list)
        # Should detect GitHub star growth
        github_momentum = [m for m in momentum if "github" in m.dimension]
        assert len(github_momentum) > 0


class TestPredictiveAnalytics:
    """Test predictive engine."""
    
    def test_forecast_trajectory(self, db_session: Session, sample_founder: Founder):
        """Test trajectory forecasting."""
        engine = PredictiveEngine(db_session)
        
        forecast = engine.forecast_trajectory(sample_founder.id, horizon_months=6)
        
        assert forecast is not None
        assert forecast.founder_id == sample_founder.id
        assert forecast.horizon_months == 6
        assert forecast.confidence >= 0.0
    
    def test_success_probability(self, db_session: Session, sample_founder: Founder):
        """Test success probability calculation."""
        engine = PredictiveEngine(db_session)
        
        prob = engine.calculate_success_probability(sample_founder.id)
        
        assert prob is not None
        assert 0.0 <= prob.product_market_fit_prob <= 1.0
        assert 0.0 <= prob.series_a_funding_prob <= 1.0
        assert isinstance(prob.key_drivers, list)
        assert isinstance(prob.risk_factors, list)
    
    def test_risk_assessment(self, db_session: Session, sample_founder: Founder):
        """Test risk assessment."""
        engine = PredictiveEngine(db_session)
        
        risk = engine.assess_risk(sample_founder.id)
        
        assert risk is not None
        assert 0.0 <= risk.overall_risk <= 1.0
        assert risk.risk_level in ("low", "medium", "high", "critical")
        assert isinstance(risk.risk_factors, list)
    
    def test_optimal_timing(self, db_session: Session, sample_founder: Founder):
        """Test timing recommendation."""
        engine = PredictiveEngine(db_session)
        
        timing = engine.determine_optimal_timing(sample_founder.id)
        
        assert timing is not None
        assert timing.recommendation in ("invest_now", "pass") or "wait_" in timing.recommendation
        assert isinstance(timing.reasoning, list)
        assert 0.0 <= timing.urgency_score <= 1.0


class TestAnomalyDetection:
    """Test anomaly detector."""
    
    def test_detect_anomalies(self, db_session: Session, sample_founder: Founder):
        """Test anomaly detection."""
        detector = AnomalyDetector(db_session)
        
        report = detector.detect_anomalies(sample_founder.id)
        
        assert report is not None
        assert report.founder_id == sample_founder.id
        assert report.overall_risk_level in ("low", "medium", "high", "critical", "unknown")
        assert report.recommended_action in ("proceed", "investigate", "flag", "reject")
        assert isinstance(report.statistical_anomalies, list)
        assert isinstance(report.behavioral_anomalies, list)
    
    def test_detect_contradictions(self, db_session: Session):
        """Test contradiction detection with conflicting signals."""
        repo = MemoryRepository(db_session)
        
        # Create founder with contradictory signals
        founder = repo.create_founder({"name": "Test Founder"})
        
        now = datetime.now(timezone.utc)
        
        # Add contradictory revenue claims
        repo.add_signal(founder.id, RawSignal(
            source="deck",
            record_type="traction_claim",
            payload={"arr": 1_000_000},
            timestamp=now,
            confidence=Confidence.CLAIMED
        ))
        
        repo.add_signal(founder.id, RawSignal(
            source="web",
            record_type="revenue",
            payload={"arr": 300_000},  # Contradiction!
            timestamp=now,
            confidence=Confidence.SCRAPED
        ))
        
        db_session.commit()
        
        # Run analysis
        analyzer = SignalCorrelationEngine(db_session)
        report = analyzer.analyze_founder_signals(founder.id)
        
        # Should detect contradiction
        assert len(report.contradictions) > 0
        assert any("arr" in c.metric.lower() for c in report.contradictions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
