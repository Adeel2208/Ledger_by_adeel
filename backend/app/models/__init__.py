"""Import all models so `Base.metadata` sees every table (for create_all / Alembic)."""
from app.models.application import Application
from app.models.company import Company
from app.models.evidence import Evidence
from app.models.founder import Founder
from app.models.memo import Claim, Memo, MemoSection
from app.models.outreach import Outreach
from app.models.score import AxisScore, FounderScore
from app.models.signal import Signal
from app.models.thesis import Thesis

__all__ = [
    "Application",
    "AxisScore",
    "Claim",
    "Company",
    "Evidence",
    "Founder",
    "FounderScore",
    "Memo",
    "MemoSection",
    "Outreach",
    "Signal",
    "Thesis",
]
