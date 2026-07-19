"""Signal — a single ingested evidence-bearing data point (Memory truth, FR-2).

Non-negotiable: every Signal carries source + timestamp + confidence + record_type.
This is the raw provenance layer dedup/enrichment operate on and evidence traces to.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    founder_id: Mapped[int | None] = mapped_column(ForeignKey("founders.id"), index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)  # github | deck:slide-4 | arxiv
    record_type: Mapped[str] = mapped_column(String(50))  # commit_activity | traction_claim
    confidence: Mapped[str] = mapped_column(String(20), default="claimed")  # verified>corroborated>claimed
    payload: Mapped[dict] = mapped_column(JSON)
    external_url: Mapped[str | None] = mapped_column(String(500))  # click-through traceability
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    founder: Mapped["Founder"] = relationship(back_populates="signals")  # noqa: F821
