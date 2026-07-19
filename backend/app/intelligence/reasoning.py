"""Multi-attribute reasoning (FR-3).

Turn a compound NL query into a structured filter + semantic query in a single
pass, then rank and explain results. e.g. "technical founder, Berlin, AI infra,
enterprise traction, no prior VC backing, top-tier accelerator".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.intelligence.retrieval import get_index
from app.llm.client import get_llm
from app.memory.repository import MemoryRepository
from app.models.application import Application
from app.models.company import Company
from app.models.founder import Founder


# Pydantic schemas for structured LLM output
class QueryEntity(BaseModel):
    """Entities extracted from the query."""
    sectors: list[str] = Field(default_factory=list, description="Industry sectors (AI, FinTech, etc.)")
    locations: list[str] = Field(default_factory=list, description="Geographic locations")
    technologies: list[str] = Field(default_factory=list, description="Tech stacks, frameworks, languages")
    accelerators: list[str] = Field(default_factory=list, description="Accelerator programs (YC, Techstars, etc.)")
    companies: list[str] = Field(default_factory=list, description="Company names")
    investors: list[str] = Field(default_factory=list, description="Investor or VC firm names")


class QueryAttribute(BaseModel):
    """Boolean attributes about founders."""
    is_technical: bool | None = Field(None, description="Has technical/engineering background")
    is_serial: bool | None = Field(None, description="Serial entrepreneur with prior ventures")
    has_exit: bool | None = Field(None, description="Has prior successful exit")
    is_cold_start: bool | None = Field(None, description="Cold-start founder (no network/history)")
    from_accelerator: bool | None = Field(None, description="Completed accelerator program")
    has_vc_backing: bool | None = Field(None, description="Has prior VC funding")
    is_hiring: bool | None = Field(None, description="Actively hiring")
    is_profitable: bool | None = Field(None, description="Currently profitable")


class QueryRange(BaseModel):
    """Numeric ranges for metrics."""
    arr_min: float | None = Field(None, description="Minimum ARR in USD")
    arr_max: float | None = Field(None, description="Maximum ARR in USD")
    users_min: int | None = Field(None, description="Minimum user count")
    users_max: int | None = Field(None, description="Maximum user count")
    team_size_min: int | None = Field(None, description="Minimum team size")
    team_size_max: int | None = Field(None, description="Maximum team size")
    github_stars_min: int | None = Field(None, description="Minimum GitHub stars")
    funding_raised_min: float | None = Field(None, description="Minimum funding raised")
    funding_raised_max: float | None = Field(None, description="Maximum funding raised")


class QueryTemporal(BaseModel):
    """Temporal constraints."""
    period: str | None = Field(None, description="Time period (last_month, last_6_months, last_year, etc.)")
    founded_after: str | None = Field(None, description="Company founded after date (YYYY-MM-DD)")
    founded_before: str | None = Field(None, description="Company founded before date (YYYY-MM-DD)")


class StructuredQuery(BaseModel):
    """Complete structured representation of a natural language query."""
    entities: QueryEntity = Field(default_factory=QueryEntity)
    attributes: QueryAttribute = Field(default_factory=QueryAttribute)
    ranges: QueryRange = Field(default_factory=QueryRange)
    temporal: QueryTemporal = Field(default_factory=QueryTemporal)
    semantic_query: str = Field("", description="Reformulated query for semantic search")
    negations: list[str] = Field(default_factory=list, description="Negated constraints (no_vc_backing, etc.)")
    confidence: float = Field(1.0, description="Parser confidence in the interpretation")


@dataclass
class SearchResult:
    """A single search result with provenance."""
    founder_id: int
    founder_name: str
    company_id: int | None
    company_name: str | None
    relevance_score: float
    match_reasons: list[str] = field(default_factory=list)
    highlights: dict[str, str] = field(default_factory=dict)
    signal_ids: list[int] = field(default_factory=list)


_PARSE_SYSTEM = """You are a query parser for a VC deal-flow system. Extract structured information from natural language queries.

Key entities to look for:
- Sectors: AI, FinTech, HealthTech, Climate, SaaS, DevTools, etc.
- Locations: city names, regions, countries
- Technologies: programming languages, frameworks, platforms
- Accelerators: Y Combinator, Techstars, 500 Startups, etc.

Boolean attributes (true/false/null):
- Technical founder, serial entrepreneur, has exit, cold-start
- From accelerator, has VC backing, hiring, profitable

Numeric ranges:
- ARR (annual recurring revenue), users, team size, GitHub stars, funding

Temporal:
- "last 6 months", "founded in 2023", "recent", etc.

Negations:
- "no prior VC", "without accelerator", "never raised" → add to negations list

Always set semantic_query to a reformulated version suitable for semantic search."""


def parse_query(natural_language: str) -> StructuredQuery:
    """Use LLM to parse natural language into structured query."""
    llm = get_llm()
    structured = llm.structured(
        natural_language,
        StructuredQuery,
        system=_PARSE_SYSTEM,
        fast=True,
    )
    return structured


def build_sql_filters(parsed: StructuredQuery, db: Session) -> list:
    """Convert parsed query into SQLAlchemy filter clauses."""
    filters = []
    
    # Entity filters
    if parsed.entities.sectors:
        filters.append(Company.sector.in_(parsed.entities.sectors))
    
    if parsed.entities.locations:
        # Partial match on geography
        location_clauses = [
            Company.geography.ilike(f"%{loc}%") for loc in parsed.entities.locations
        ]
        filters.append(or_(*location_clauses))
    
    # Attribute filters
    if parsed.attributes.is_technical is not None:
        # Technical founders have GitHub signals
        if parsed.attributes.is_technical:
            filters.append(Founder.github_handle.isnot(None))
        else:
            filters.append(Founder.github_handle.is_(None))
    
    if parsed.attributes.is_cold_start is not None:
        filters.append(Founder.is_cold_start == parsed.attributes.is_cold_start)
    
    # Range filters (will need to join signals for metrics)
    # For now, we'll handle these in post-filtering
    
    # Negations
    if "no_vc_backing" in parsed.negations or parsed.attributes.has_vc_backing is False:
        # Founders with no funding signals
        pass  # Handle in post-filter
    
    return filters


def execute_hybrid_search(
    parsed: StructuredQuery,
    db: Session,
    k: int = 50
) -> list[SearchResult]:
    """Execute multi-stage search: SQL filters → semantic search → ranking."""
    repo = MemoryRepository(db)
    
    # Stage 1: SQL filters (deterministic attributes)
    sql_filters = build_sql_filters(parsed, db)
    
    # Base query: join Founder → Application → Company
    query = (
        select(Founder, Application, Company)
        .join(Application, Founder.id == Application.founder_id, isouter=True)
        .join(Company, Application.company_id == Company.id, isouter=True)
    )
    
    if sql_filters:
        query = query.where(and_(*sql_filters))
    
    # Execute and get candidates
    candidates = db.execute(query).all()
    
    # Stage 2: Semantic search over signals if there's a semantic component
    semantic_matches = {}
    if parsed.semantic_query:
        vector_results = get_index().query(parsed.semantic_query, k=k * 2)
        for result in vector_results:
            # Extract founder_id from metadata
            founder_id = result.get("metadata", {}).get("founder_id")
            if founder_id:
                semantic_matches[founder_id] = result["score"]
    
    # Stage 3: Score and rank results
    results = []
    for founder, application, company in candidates:
        if not founder:
            continue
        
        # Calculate relevance score
        relevance = 0.0
        match_reasons = []
        
        # SQL filter match (base relevance)
        relevance += 0.3
        match_reasons.append("Matches structural filters")
        
        # Semantic match boost
        if founder.id in semantic_matches:
            semantic_score = semantic_matches[founder.id]
            relevance += semantic_score * 0.5
            match_reasons.append(f"Semantic similarity: {semantic_score:.2f}")
        
        # Exact entity matches (boost)
        if company and parsed.entities.sectors:
            if company.sector in parsed.entities.sectors:
                relevance += 0.2
                match_reasons.append(f"Sector match: {company.sector}")
        
        # Signal count boost (more data = higher confidence)
        signal_count = len(repo.signals_for(founder.id))
        if signal_count > 0:
            relevance += min(0.2, signal_count / 50)  # Cap at 0.2
            match_reasons.append(f"{signal_count} signals available")
        
        # Create result
        results.append(
            SearchResult(
                founder_id=founder.id,
                founder_name=founder.name,
                company_id=company.id if company else None,
                company_name=company.name if company else None,
                relevance_score=min(1.0, relevance),
                match_reasons=match_reasons,
                highlights={
                    "sector": company.sector if company else None,
                    "location": company.geography if company else None,
                    "github": founder.github_handle,
                },
                signal_ids=[s.id for s in repo.signals_for(founder.id)[:5]],
            )
        )
    
    # Sort by relevance
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    # Apply range filters in post-processing
    filtered_results = apply_range_filters(results, parsed, repo, db)
    
    return filtered_results[:k]


def apply_range_filters(
    results: list[SearchResult],
    parsed: StructuredQuery,
    repo: MemoryRepository,
    db: Session
) -> list[SearchResult]:
    """Post-filter results based on numeric ranges extracted from signals."""
    if not any([
        parsed.ranges.arr_min,
        parsed.ranges.users_min,
        parsed.ranges.github_stars_min,
        parsed.ranges.team_size_min,
    ]):
        return results  # No range filters
    
    filtered = []
    for result in results:
        signals = repo.signals_for(result.founder_id)
        
        # Extract metrics from signals
        metrics = extract_metrics_from_signals(signals)
        
        # Check range constraints
        passes = True
        
        if parsed.ranges.arr_min and metrics.get("arr", 0) < parsed.ranges.arr_min:
            passes = False
        if parsed.ranges.arr_max and metrics.get("arr", 0) > parsed.ranges.arr_max:
            passes = False
        
        if parsed.ranges.users_min and metrics.get("users", 0) < parsed.ranges.users_min:
            passes = False
        
        if parsed.ranges.github_stars_min and metrics.get("github_stars", 0) < parsed.ranges.github_stars_min:
            passes = False
        
        if passes:
            # Add metric info to match reasons
            if metrics:
                result.match_reasons.append(f"Metrics: {metrics}")
            filtered.append(result)
    
    return filtered


def extract_metrics_from_signals(signals: list) -> dict[str, float]:
    """Extract key metrics from signals."""
    metrics = {}
    
    for signal in signals:
        payload = signal.payload
        
        # ARR/MRR
        if "arr" in payload:
            metrics["arr"] = float(payload["arr"])
        elif "mrr" in payload:
            metrics["arr"] = float(payload["mrr"]) * 12
        
        # Users
        if "users" in payload or "user_count" in payload:
            metrics["users"] = int(payload.get("users", payload.get("user_count", 0)))
        
        # GitHub stars
        if signal.record_type == "github_profile":
            metrics["github_stars"] = int(payload.get("total_stars", 0))
        
        # Team size
        if "team_size" in payload or "employees" in payload:
            metrics["team_size"] = int(payload.get("team_size", payload.get("employees", 0)))
    
    return metrics


def resolve_query(natural_language: str, db: Session, k: int = 50) -> dict:
    """Main entry point: NL query → structured → results."""
    # Parse query
    parsed = parse_query(natural_language)
    
    # Execute search
    results = execute_hybrid_search(parsed, db, k=k)
    
    # Format response
    return {
        "query": natural_language,
        "parsed": parsed.model_dump(),
        "results": [
            {
                "founder_id": r.founder_id,
                "founder_name": r.founder_name,
                "company_id": r.company_id,
                "company_name": r.company_name,
                "relevance_score": r.relevance_score,
                "match_reasons": r.match_reasons,
                "highlights": r.highlights,
            }
            for r in results
        ],
        "total": len(results),
    }
