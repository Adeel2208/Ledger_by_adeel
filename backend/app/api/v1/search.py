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
from app.memory.repository import MemoryRepository
from app.services import profile_service

router = APIRouter()


def _attach_avatars(payload: dict, db: Session) -> dict:
    """Decorate each result row with the founder's avatar block.

    Done here rather than inside `resolve_query` so the reasoning layer stays
    presentation-free — the same search core can serve callers that don't
    render faces.
    """
    repo = MemoryRepository(db)
    for row in payload.get("results", []):
        founder = repo.get_founder(row["founder_id"])
        if founder is not None:
            row["avatar"] = profile_service.avatar_block(founder)
    return payload


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
    return _attach_avatars(resolve_query(req.query, db, k=req.k), db)


@router.post("/simple")
def simple_search(req: SimpleSearchRequest) -> list[dict]:
    """
    Simple semantic search over signals (legacy endpoint).
    
    Use /search for advanced natural language queries.
    """
    return get_index().query(req.query, k=req.k)
