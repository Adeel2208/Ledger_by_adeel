"""Market intelligence engine for deep competitive and market analysis.

Provides real-time market insights, competitive landscape mapping,
and market timing assessment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.memory.ingestion.tavily import TavilyConnector


@dataclass
class Competitor:
    """Competitive company information."""
    name: str
    description: str
    funding: str | None
    stage: str | None
    url: str | None
    strengths: list[str] = field(default_factory=list)


@dataclass
class CompetitiveLandscape:
    """Complete competitive analysis."""
    direct_competitors: list[Competitor]
    indirect_competitors: list[Competitor]
    market_concentration: str  # fragmented, moderate, concentrated
    white_spaces: list[str]
    competitive_advantages: list[str]
    threats: list[str]


@dataclass
class MarketTiming:
    """Market timing assessment."""
    timing_score: float  # 0-1, higher = better timing
    stage_in_cycle: str  # early, growth, mature, declining
    catalyst_events: list[str]
    risks: list[str]
    opportunity_window: str  # months/years


@dataclass
class TAMAnalysis:
    """Total Addressable Market analysis."""
    tam_estimate: float  # USD
    sam_estimate: float  # Serviceable Available Market
    som_estimate: float  # Serviceable Obtainable Market
    growth_rate: float  # annual %
    confidence: str  # low, medium, high
    sources: list[str]
    methodology: str


@dataclass
class MarketIntelligence:
    """Complete market intelligence report."""
    sector: str
    geography: str
    competitive_landscape: CompetitiveLandscape
    market_timing: MarketTiming
    tam_analysis: TAMAnalysis
    overall_attractiveness: float  # 0-1
    recommendation: str
    generated_at: datetime


class MarketIntelligenceEngine:
    """Provides deep market intelligence."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tavily = TavilyConnector()
    
    def analyze_market(
        self,
        sector: str,
        geography: str,
        company_name: str | None = None
    ) -> MarketIntelligence:
        """Complete market analysis."""
        # Gather intelligence from multiple angles
        competitive = self.map_competitive_landscape(sector, company_name)
        timing = self.assess_market_timing(sector)
        tam = self.analyze_tam(sector, geography)
        
        # Calculate overall attractiveness
        attractiveness = self._calculate_attractiveness(competitive, timing, tam)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            attractiveness, competitive, timing
        )
        
        return MarketIntelligence(
            sector=sector,
            geography=geography,
            competitive_landscape=competitive,
            market_timing=timing,
            tam_analysis=tam,
            overall_attractiveness=attractiveness,
            recommendation=recommendation,
            generated_at=datetime.now(timezone.utc),
        )
    
    def map_competitive_landscape(
        self,
        sector: str,
        company_name: str | None = None
    ) -> CompetitiveLandscape:
        """Map the competitive landscape."""
        # Search for competitors
        query = f"{sector} startups companies competitors landscape"
        if company_name:
            query += f" {company_name} alternatives"
        
        signals = self.tavily.fetch(query=query, max_results=15)
        
        # Extract competitor information
        competitors = self._extract_competitors(signals.signals, sector)
        
        # Categorize as direct vs indirect
        direct = [c for c in competitors if self._is_direct_competitor(c, sector)]
        indirect = [c for c in competitors if c not in direct]
        
        # Assess market concentration
        concentration = self._assess_concentration(len(competitors))
        
        # Identify white spaces
        white_spaces = self._identify_white_spaces(competitors, sector)
        
        # Competitive advantages
        advantages = self._identify_advantages(competitors, company_name)
        
        # Threats
        threats = self._identify_threats(competitors)
        
        return CompetitiveLandscape(
            direct_competitors=direct[:10],
            indirect_competitors=indirect[:5],
            market_concentration=concentration,
            white_spaces=white_spaces,
            competitive_advantages=advantages,
            threats=threats,
        )
    
    def assess_market_timing(self, sector: str) -> MarketTiming:
        """Assess market timing and cycle stage."""
        # Search for market trends and news
        query = f"{sector} market trends growth investment 2026"
        signals = self.tavily.fetch(query=query, max_results=10)
        
        # Analyze signals for timing indicators
        catalyst_events = []
        risks = []
        
        for signal in signals.signals:
            text = signal.text or ""
            text_lower = text.lower()
            
            # Look for catalysts
            if any(word in text_lower for word in ['growth', 'expanding', 'emerging', 'hot']):
                catalyst_events.append(text[:100])
            
            # Look for risks
            if any(word in text_lower for word in ['decline', 'challenge', 'saturated', 'competitive']):
                risks.append(text[:100])
        
        # Determine cycle stage (simplified heuristic)
        catalyst_count = len(catalyst_events)
        risk_count = len(risks)
        
        if catalyst_count > risk_count * 2:
            stage = "early"
            timing_score = 0.8
        elif catalyst_count > risk_count:
            stage = "growth"
            timing_score = 0.7
        elif risk_count > catalyst_count * 2:
            stage = "declining"
            timing_score = 0.3
        else:
            stage = "mature"
            timing_score = 0.5
        
        # Opportunity window
        if stage == "early":
            window = "12-24 months"
        elif stage == "growth":
            window = "6-18 months"
        else:
            window = "3-6 months"
        
        return MarketTiming(
            timing_score=timing_score,
            stage_in_cycle=stage,
            catalyst_events=catalyst_events[:5],
            risks=risks[:5],
            opportunity_window=window,
        )
    
    def analyze_tam(self, sector: str, geography: str) -> TAMAnalysis:
        """Analyze Total Addressable Market."""
        # Search for market size data
        query = f"{sector} market size {geography} TAM SAM 2026"
        signals = self.tavily.fetch(query=query, max_results=10)
        
        # Extract market size estimates
        tam_estimate = self._extract_market_size(signals.signals)
        
        # SAM is typically 10-30% of TAM
        sam_estimate = tam_estimate * 0.2
        
        # SOM is typically 5-10% of SAM for startups
        som_estimate = sam_estimate * 0.08
        
        # Growth rate (simplified)
        growth_rate = 15.0  # Default assumption
        
        # Determine confidence based on signal quality
        confidence = "medium" if len(signals.signals) >= 5 else "low"
        
        sources = [s.external_url for s in signals.signals if s.external_url][:5]
        
        return TAMAnalysis(
            tam_estimate=tam_estimate,
            sam_estimate=sam_estimate,
            som_estimate=som_estimate,
            growth_rate=growth_rate,
            confidence=confidence,
            sources=sources,
            methodology="web_research"
        )
    
    # Helper methods
    
    def _extract_competitors(
        self, signals: list, sector: str
    ) -> list[Competitor]:
        """Extract competitor information from signals."""
        competitors = []
        seen_names = set()
        
        for signal in signals:
            text = signal.text or ""
            payload = signal.payload
            
            # Simple extraction (would use NER in production)
            if "company" in payload or "competitor" in text.lower():
                name = payload.get("title", "Unknown")[:50]
                
                if name not in seen_names:
                    competitors.append(Competitor(
                        name=name,
                        description=text[:200],
                        funding=None,  # Would extract
                        stage=None,
                        url=signal.external_url,
                        strengths=[],
                    ))
                    seen_names.add(name)
        
        return competitors[:15]
    
    def _is_direct_competitor(self, competitor: Competitor, sector: str) -> bool:
        """Determine if competitor is direct vs indirect."""
        # Simple heuristic: check if sector appears in description
        return sector.lower() in competitor.description.lower()
    
    def _assess_concentration(self, competitor_count: int) -> str:
        """Assess market concentration level."""
        if competitor_count < 5:
            return "concentrated"
        elif competitor_count < 15:
            return "moderate"
        else:
            return "fragmented"
    
    def _identify_white_spaces(
        self, competitors: list[Competitor], sector: str
    ) -> list[str]:
        """Identify market white spaces."""
        # Simplified: look for underserved segments
        white_spaces = []
        
        # Common white space patterns
        if len(competitors) < 10:
            white_spaces.append("Emerging market with room for new entrants")
        
        # Would analyze competitor positioning to find gaps
        white_spaces.append("Niche verticals may be underserved")
        
        return white_spaces
    
    def _identify_advantages(
        self, competitors: list[Competitor], company_name: str | None
    ) -> list[str]:
        """Identify potential competitive advantages."""
        advantages = []
        
        if len(competitors) > 20:
            advantages.append("Differentiation critical in crowded market")
        else:
            advantages.append("First-mover advantage possible")
        
        advantages.append("Technology innovation")
        advantages.append("Superior user experience")
        
        return advantages
    
    def _identify_threats(self, competitors: list[Competitor]) -> list[str]:
        """Identify competitive threats."""
        threats = []
        
        if len(competitors) > 15:
            threats.append("Highly competitive landscape")
        
        threats.append("Established incumbents may enter space")
        threats.append("Price competition risk")
        
        return threats
    
    def _extract_market_size(self, signals: list) -> float:
        """Extract market size from signals."""
        # Look for numbers + billion/million
        import re
        
        for signal in signals:
            text = signal.text or ""
            
            # Pattern: $X billion, $X million
            patterns = [
                r'\$(\d+(?:\.\d+)?)\s*billion',
                r'\$(\d+(?:\.\d+)?)\s*million',
                r'(\d+(?:\.\d+)?)\s*billion',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    if 'billion' in pattern:
                        return value * 1_000_000_000
                    else:
                        return value * 1_000_000
        
        # Default estimate
        return 5_000_000_000  # $5B default
    
    def _calculate_attractiveness(
        self,
        competitive: CompetitiveLandscape,
        timing: MarketTiming,
        tam: TAMAnalysis
    ) -> float:
        """Calculate overall market attractiveness (0-1)."""
        # Weight different factors
        score = 0.0
        
        # TAM size (larger is better, up to a point)
        if tam.tam_estimate > 10_000_000_000:  # >$10B
            score += 0.3
        elif tam.tam_estimate > 1_000_000_000:  # >$1B
            score += 0.2
        else:
            score += 0.1
        
        # Growth rate
        if tam.growth_rate > 20:
            score += 0.2
        elif tam.growth_rate > 10:
            score += 0.15
        else:
            score += 0.05
        
        # Timing score
        score += timing.timing_score * 0.3
        
        # Competition (moderate is best)
        if competitive.market_concentration == "moderate":
            score += 0.2
        elif competitive.market_concentration == "fragmented":
            score += 0.15
        else:  # concentrated
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_recommendation(
        self,
        attractiveness: float,
        competitive: CompetitiveLandscape,
        timing: MarketTiming
    ) -> str:
        """Generate investment recommendation."""
        if attractiveness > 0.7 and timing.timing_score > 0.6:
            return "Highly attractive market - strong investment opportunity"
        elif attractiveness > 0.5:
            return "Moderately attractive - proceed with strong differentiation"
        elif attractiveness > 0.3:
            return "Challenging market - high differentiation required"
        else:
            return "Unattractive market conditions - reconsider"
