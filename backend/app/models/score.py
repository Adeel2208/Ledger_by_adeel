"""Scores — persistent Founder Score history + per-application axis scores.

AxisScore: the three INDEPENDENT axes (never averaged). Multiple rows over time
per axis give the trend direction.
FounderScore: persistent, versioned, cross-application — NEVER reset (FR-7).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AxisScore(Base):
    __tablename__ = "axis_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    axis: Mapped[str] = mapped_column(String(20))  # founder | market | idea (never a composite)
    value: Mapped[float] = mapped_column(Float)
    trend: Mapped[str | None] = mapped_column(String(20))  # improving | stable | declining
    rationale: Mapped[str | None] = mapped_column(String(2000))
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="scores")  # noqa: F821


class FounderScore(Base):
    __tablename__ = "founder_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    founder_id: Mapped[int] = mapped_column(ForeignKey("founders.id"), index=True)
    value: Mapped[float] = mapped_column(Float)
    momentum: Mapped[str | None] = mapped_column(String(20))
    components: Mapped[dict] = mapped_column(JSON, default=dict)  # technical/execution/comm/vision/resilience
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    founder: Mapped["Founder"] = relationship(back_populates="score_history")  # noqa: F821
