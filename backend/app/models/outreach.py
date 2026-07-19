"""Outreach (FR-5, D3) — tracks activation of outbound-discovered founders."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(primary_key=True)
    founder_id: Mapped[int] = mapped_column(ForeignKey("founders.id"), index=True)
    channel: Mapped[str] = mapped_column(String(50))  # email | linkedin
    status: Mapped[str] = mapped_column(String(30), default="discovered")  # discovered|contacted|activated
