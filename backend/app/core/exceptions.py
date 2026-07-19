"""Domain exceptions + FastAPI handlers."""
from __future__ import annotations


class VCBrainError(Exception):
    """Base class for all application errors."""


class NotFoundError(VCBrainError):
    ...
