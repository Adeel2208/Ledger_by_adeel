"""OpenAI implementation of LLMProvider.

Uses `chat.completions.parse` with a Pydantic `response_format` so every
structured call returns schema-valid data (OpenAI Structured Outputs). Transient
errors are retried with exponential backoff.

Model-compatibility note: frontier reasoning models (gpt-5.x) only accept the
default temperature. We attempt with the requested temperature and, if the model
rejects it, transparently retry without the parameter — so the same code works
across gpt-4o and gpt-5.x without per-model branching.
"""
from __future__ import annotations

import logging

from openai import BadRequestError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.llm.base import LLMProvider, T

logger = logging.getLogger(__name__)

_RETRY = retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    reraise=True,
)


def _unsupported_temperature(exc: BadRequestError) -> bool:
    return "temperature" in str(exc).lower()


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import OpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model
        self._model_fast = settings.llm_model_fast

    def _pick(self, fast: bool) -> str:
        return self._model_fast if fast else self._model

    @staticmethod
    def _messages(prompt: str, system: str | None) -> list[dict]:
        msgs: list[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def _with_temp_fallback(self, fn, *, temperature: float, **kwargs):
        """Call `fn` with temperature; retry without it if the model rejects it."""
        try:
            return fn(temperature=temperature, **kwargs)
        except BadRequestError as exc:
            if _unsupported_temperature(exc):
                return fn(**kwargs)  # let the model use its default temperature
            raise

    @_RETRY
    def complete(
        self, prompt: str, *, system: str | None = None, temperature: float = 0.2, fast: bool = False
    ) -> str:
        resp = self._with_temp_fallback(
            self._client.chat.completions.create,
            temperature=temperature,
            model=self._pick(fast),
            messages=self._messages(prompt, system),
        )
        return resp.choices[0].message.content or ""

    @_RETRY
    def structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        fast: bool = False,
    ) -> T:
        completion = self._with_temp_fallback(
            self._client.chat.completions.parse,
            temperature=temperature,
            model=self._pick(fast),
            messages=self._messages(prompt, system),
            response_format=schema,
        )
        message = completion.choices[0].message
        if message.refusal:
            raise RuntimeError(f"Model refused structured request: {message.refusal}")
        parsed = message.parsed
        if parsed is None:  # pragma: no cover - defensive
            raise RuntimeError("Structured parse returned no content.")
        return parsed
