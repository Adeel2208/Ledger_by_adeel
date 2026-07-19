"""Aggregate v1 router — the single mount point for the Experience layer.

Each domain router is thin: validate input, call a service, return a DTO.
No business logic lives here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    applications,
    dashboard,
    founders,
    memos,
    scores,
    search,
    sourcing,
    thesis,
)

api_router = APIRouter()
api_router.include_router(thesis.router, prefix="/thesis", tags=["thesis"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(founders.router, prefix="/founders", tags=["founders"])
api_router.include_router(sourcing.router, prefix="/sourcing", tags=["sourcing"])
api_router.include_router(scores.router, prefix="/opportunities", tags=["scores"])
api_router.include_router(memos.router, prefix="/memos", tags=["memos"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
