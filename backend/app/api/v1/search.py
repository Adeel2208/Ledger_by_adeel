"""Advanced multi-attribute search with natural language understanding (FR-3).

Full NL compound-query resolver with hybrid search (vector + SQL filters),
intelligent ranking, and explainable results.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.intelligence.reasoning import resolve_query
from app.intelligence.retrieval import get_index

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    k: int = Field(default=50, description="Max results to return")
    filters: dict = Field(default_factory=dict, description="Additional filters")


class SimpleSearchRequest(BaseModel):
    query: str
    k: int = 10


@router.post("")
def advanced_search(req: SearchRequest, db: Session = Depends(get_db)) -> dict:
    """
    Advanced multi-attribute search with natural language understanding.
    
    Supports complex queries like:
    - "technical founder in Berlin working on AI infrastructure"
    - "serial entrepreneur, no prior VC, raised <$2M, growing >20% MoM"
    - "YC alum, GitHub stars >5K, hiring in SF, seed stage"
    
    Returns structured results with relevance scoring and match explanations.
    """
    return resolve_query(req.query, db, k=req.k)


@router.post("/simple")
def simple_search(req: SimpleSearchRequest) -> list[dict]:
    """
    Simple semantic search over signals (legacy endpoint).
    
    Use /search for advanced natural language queries.
    """
    return get_index().query(req.query, k=req.k)
