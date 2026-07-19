"""Signal DTOs — the transport shape of an ingested evidence point.

`SignalIn` is what connectors emit; `SignalOut` is what the API returns. Both
always carry provenance (source + timestamp + confidence + record_type).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Confidence


class SignalIn(BaseModel):
    source: str
    record_type: str
    payload: dict[str, Any]
    source_timestamp: datetime
    confidence: Confidence = Confidence.CLAIMED
    external_url: str | None = None
    # Human-readable text used for embedding + semantic search.
    text: str | None = None


class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    founder_id: int | None
    source: str
    record_type: str
    confidence: str
    payload: dict[str, Any]
    external_url: str | None
    source_timestamp: datetime
    ingested_at: datetime
