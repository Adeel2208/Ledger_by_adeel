"""Application / Opportunity — one founder pitching one company through the pipeline.

Source channel (inbound|outbound) is recorded but MUST NOT affect scoring (D2).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    founder_id: Mapped[int] = mapped_column(ForeignKey("founders.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    channel: Mapped[str] = mapped_column(String(20))  # inbound | outbound
    stage: Mapped[str] = mapped_column(String(20), default="sourced")
    screening_decision: Mapped[str | None] = mapped_column(String(20))  # pass|fail|review
    screening_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    founder: Mapped["Founder"] = relationship(back_populates="applications")  # noqa: F821
    scores: Mapped[list["AxisScore"]] = relationship(back_populates="application")  # noqa: F821
