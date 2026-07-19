"""Embeddings — provider-abstracted, feeds the vector index in `intelligence/retrieval.py`.

Kept separate from the chat provider because the best embedding model and the
best reasoning model may come from different vendors. Default: OpenAI
text-embedding-3-large (dimension-shortened for cost/quality balance).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

_RETRY = retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=20), reraise=True)


class Embedder(ABC):
    dimensions: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text (order preserved)."""

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class OpenAIEmbedder(Embedder):
    def __init__(self) -> None:
        from openai import OpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    @_RETRY
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Normalise whitespace; OpenAI rejects empty strings.
        cleaned = [t.strip() or " " for t in texts]
        resp = self._client.embeddings.create(
            model=self._model, input=cleaned, dimensions=self.dimensions
        )
        return [d.embedding for d in resp.data]


@lru_cache
def get_embedder() -> Embedder:
    provider = get_settings().embedding_provider.lower()
    if provider == "openai":
        return OpenAIEmbedder()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider!r}")
