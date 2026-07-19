"""LLM factory — resolves the configured provider into an `LLMProvider`.

Usage:
    from app.llm.client import get_llm
    llm = get_llm()
    result = llm.structured(prompt, MarketScoreSchema)
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider


@lru_cache
def get_llm() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider()

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
