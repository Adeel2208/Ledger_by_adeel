"""Provider-agnostic LLM contract.

Every model call in the system goes through this interface, so switching
OpenAI <-> Anthropic is a config change (LLM_PROVIDER), never a code change.
All *reasoning* outputs are structured JSON validated against a Pydantic schema
(principle #4) — scores and memos must be machine-renderable and testable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Interface both OpenAI and Anthropic providers implement.

    `fast=True` routes to the cheap/high-volume model (extraction, screening);
    `fast=False` (default) uses the frontier reasoning model (scoring, memos).
    """

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        fast: bool = False,
    ) -> str:
        """Free-text completion (used sparingly — prefer `structured`)."""

    @abstractmethod
    def structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        fast: bool = False,
    ) -> T:
        """Completion coerced into and validated against `schema`.

        Primary entry point: scorers, extractors, and the memo generator call it
        so the UI can render results programmatically and tests can assert fields.
        """
