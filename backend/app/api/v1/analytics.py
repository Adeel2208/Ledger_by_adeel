"""Sourcing & channel intelligence endpoints (stretch I3)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import channel_performance

router = APIRouter()


@router.get("/channels")
def channels(db: Session = Depends(get_db)) -> dict:
    """Which sourcing channels produce the strongest opportunities + what to try next."""
    return channel_performance(db)
