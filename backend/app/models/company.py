"""Company — a specific venture a founder is building (many per founder over time)."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    sector: Mapped[str | None] = mapped_column(String(100))
    stage: Mapped[str | None] = mapped_column(String(50))  # pre-seed | seed | series-a
    geography: Mapped[str | None] = mapped_column(String(100))
    domain: Mapped[str | None] = mapped_column(String(200))
