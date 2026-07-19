"""Investment memo (FR-9) — sections -> claims, each claim linked to evidence.

Required sections: company snapshot, investment hypotheses, SWOT, problem & product,
traction & KPIs. Optional sections included only where data exists; gaps flagged.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Memo(Base):
    __tablename__ = "memos"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    recommendation: Mapped[str | None] = mapped_column(String(20))  # invest | pass | need_more_info
    trust_score: Mapped[float | None] = mapped_column(Float)  # 0-100 data-quality assessment
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sections: Mapped[list["MemoSection"]] = relationship(back_populates="memo")


class MemoSection(Base):
    __tablename__ = "memo_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    memo_id: Mapped[int] = mapped_column(ForeignKey("memos.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    is_gap: Mapped[bool] = mapped_column(default=False)  # explicitly-flagged missing data, never fabricated

    memo: Mapped["Memo"] = relationship(back_populates="sections")
    claims: Mapped[list["Claim"]] = relationship(back_populates="section")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("memo_sections.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(20), default="claimed")
    contradicted: Mapped[bool] = mapped_column(default=False)  # flagged by contradiction detector

    section: Mapped["MemoSection"] = relationship(back_populates="claims")
