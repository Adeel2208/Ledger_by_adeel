"""Anthropic implementation of LLMProvider (default provider).

Uses tool-forcing / JSON parsing to guarantee schema-valid structured output.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.llm.base import LLMProvider, T


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        # from anthropic import Anthropic
        # from app.core.config import get_settings
        # s = get_settings()
        # self._client = Anthropic(api_key=s.anthropic_api_key)
        # self._model = s.llm_model
        raise NotImplementedError("Wire up the Anthropic SDK client.")

    def complete(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        raise NotImplementedError

    def structured(
        self, prompt: str, schema: type[T], *, system: str | None = None, temperature: float = 0.0
    ) -> T:
        # Force a tool/JSON response, then `schema.model_validate_json(...)`.
        raise NotImplementedError
