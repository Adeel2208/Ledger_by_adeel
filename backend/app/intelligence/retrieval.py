"""Vector retrieval over signals — provider-abstracted (Chroma dev / pgvector prod).

An INDEX over the relational truth in Memory, never the source of truth itself.
Retrieval namespaces are kept explicit via `collection` so signal-level semantic
search never bleeds into other embedding spaces.

We compute embeddings ourselves (app.llm.embeddings) and pass vectors in, so the
embedding model is controlled centrally rather than by the vector store.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import get_settings
from app.llm.embeddings import get_embedder


class VectorIndex(ABC):
    @abstractmethod
    def upsert(self, ids: list[str], texts: list[str], metadata: list[dict]) -> None:
        """Embed `texts` and upsert under `ids` with attached `metadata`."""

    @abstractmethod
    def query(self, text: str, k: int = 10, where: dict | None = None) -> list[dict]:
        """Semantic search; returns [{id, score, metadata}] best-first."""

    @abstractmethod
    def delete(self, ids: list[str]) -> None: ...


class ChromaIndex(VectorIndex):
    """Local persistent Chroma collection. Good enough for dev + the demo."""

    def __init__(self, collection: str = "signals") -> None:
        import chromadb

        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_dir)
        # We supply embeddings explicitly, so no embedding_function here.
        self._col = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )
        self._embedder = get_embedder()

    def upsert(self, ids: list[str], texts: list[str], metadata: list[dict]) -> None:
        if not ids:
            return
        vectors = self._embedder.embed(texts)
        self._col.upsert(ids=ids, embeddings=vectors, documents=texts, metadatas=metadata)

    def query(self, text: str, k: int = 10, where: dict | None = None) -> list[dict]:
        vector = self._embedder.embed_one(text)
        res = self._col.query(query_embeddings=[vector], n_results=k, where=where)
        out: list[dict] = []
        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        for i, _id in enumerate(ids):
            # cosine distance -> similarity score
            out.append({"id": _id, "score": 1.0 - distances[i], "metadata": metadatas[i]})
        return out

    def delete(self, ids: list[str]) -> None:
        if ids:
            self._col.delete(ids=ids)


@lru_cache
def get_index(collection: str = "signals") -> VectorIndex:
    backend = get_settings().vector_backend.lower()
    if backend == "chroma":
        return ChromaIndex(collection)
    # pgvector implementation slots in here for prod without touching callers.
    raise ValueError(f"Unsupported VECTOR_BACKEND: {backend!r}")
