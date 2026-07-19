"""Evidence — links a memo Claim to the exact Signal(s) that back it (FR-8, I1).

A claim marked 'verified' MUST have >=1 Evidence row. This table is what makes
"honesty by construction" real: no evidence -> cannot be verified.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), index=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    confidence: Mapped[str] = mapped_column(String(20))  # verified | corroborated | claimed
    note: Mapped[str | None] = mapped_column(String(500))
