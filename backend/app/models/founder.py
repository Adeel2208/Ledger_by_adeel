"""Founder — the STABLE ROOT entity (founder-centric model, FR-7).

The founder outlives any single company/application, which is what makes the
persistent Founder Score possible. One founder -> many applications/companies.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Founder(Base):
    __tablename__ = "founders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str | None] = mapped_column(String(200), index=True)
    github_handle: Mapped[str | None] = mapped_column(String(100), index=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(300))
    is_cold_start: Mapped[bool] = mapped_column(default=False)  # scored via alternate method
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applications: Mapped[list["Application"]] = relationship(back_populates="founder")  # noqa: F821
    signals: Mapped[list["Signal"]] = relationship(back_populates="founder")  # noqa: F821
    score_history: Mapped[list["FounderScore"]] = relationship(back_populates="founder")  # noqa: F821
