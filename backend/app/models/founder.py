"""Founder — the STABLE ROOT entity (founder-centric model, FR-7).

The founder outlives any single company/application, which is what makes the
persistent Founder Score possible. One founder -> many applications/companies.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
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

    # ── Profile (founder-supplied, consented) ─────────────────────────────────
    # Every field below is optional by design: an unset field is a *disclosed
    # gap*, never a fabricated value (honesty-over-completeness). Outbound-
    # discovered founders legitimately have all of these empty until they
    # submit them themselves.
    photo_path: Mapped[str | None] = mapped_column(String(300))   # relative to data/uploads
    headline: Mapped[str | None] = mapped_column(String(160))     # "Founder & CTO, Acme"
    bio: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(String(120))
    location: Mapped[str | None] = mapped_column(String(160))
    personal_url: Mapped[str | None] = mapped_column(String(300))
    twitter_handle: Mapped[str | None] = mapped_column(String(100))
    # [{"company","title","start","end","summary"}] — ordered most-recent-first.
    work_history: Mapped[list | None] = mapped_column(JSON)
    profile_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    applications: Mapped[list["Application"]] = relationship(back_populates="founder")  # noqa: F821
    signals: Mapped[list["Signal"]] = relationship(back_populates="founder")  # noqa: F821
    score_history: Mapped[list["FounderScore"]] = relationship(back_populates="founder")  # noqa: F821
