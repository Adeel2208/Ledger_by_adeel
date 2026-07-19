"""Investment thesis (FR-1) — versioned, runtime-configurable, never hardcoded."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Thesis(Base):
    __tablename__ = "theses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="default")
    sectors: Mapped[list] = mapped_column(JSON, default=list)
    stages: Mapped[list] = mapped_column(JSON, default=list)
    geographies: Mapped[list] = mapped_column(JSON, default=list)
    check_size_min: Mapped[int | None] = mapped_column(Integer)
    check_size_max: Mapped[int | None] = mapped_column(Integer)
    ownership_target: Mapped[float | None] = mapped_column(Float)
    risk_appetite: Mapped[str] = mapped_column(String(20), default="moderate")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
