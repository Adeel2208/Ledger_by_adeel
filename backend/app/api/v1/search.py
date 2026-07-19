"""Semantic search over the Memory layer (foundation for FR-3 multi-attribute reasoning).

For now: vector search over signals. The full NL compound-query resolver
(intelligence/reasoning.py) builds on top of this retrieval primitive.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.intelligence.retrieval import get_index

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    k: int = 10


@router.post("")
def search(req: SearchRequest) -> list[dict]:
    """Semantic search across ingested signals; returns matches with provenance."""
    return get_index().query(req.query, k=req.k)
