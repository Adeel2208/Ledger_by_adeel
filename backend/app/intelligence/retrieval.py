"""Hybrid retrieval over signals — BM25 + Dense vectors (Chroma dev / pgvector prod).

An INDEX over the relational truth in Memory, never the source of truth itself.
Retrieval namespaces are kept explicit via `collection` so signal-level semantic
search never bleeds into other embedding spaces.

Hybrid search combines:
- BM25 (sparse, keyword-based) for exact term matches
- Dense embeddings for semantic similarity
- Reciprocal Rank Fusion (RRF) for result merging

We compute embeddings ourselves (app.llm.embeddings) and pass vectors in, so the
embedding model is controlled centrally rather than by the vector store.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import lru_cache
from typing import Any

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


class BM25Index:
    """Sparse keyword-based search using BM25 algorithm."""
    
    def __init__(self):
        self.documents: dict[str, str] = {}  # id -> text
        self.doc_metadata: dict[str, dict] = {}  # id -> metadata
        self._index_built = False
        self._term_doc_freq: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._doc_lengths: dict[str, int] = {}
        self._avg_doc_length = 0.0
        
        # BM25 parameters
        self.k1 = 1.5  # term frequency saturation
        self.b = 0.75  # length normalization
    
    def upsert(self, ids: list[str], texts: list[str], metadata: list[dict]) -> None:
        """Add or update documents in the BM25 index."""
        for doc_id, text, meta in zip(ids, texts, metadata):
            self.documents[doc_id] = text
            self.doc_metadata[doc_id] = meta
            
            # Tokenize and update term frequencies
            terms = self._tokenize(text)
            self._doc_lengths[doc_id] = len(terms)
            
            for term in set(terms):
                self._term_doc_freq[term][doc_id] = terms.count(term)
        
        # Recalculate average document length
        if self.documents:
            self._avg_doc_length = sum(self._doc_lengths.values()) / len(self.documents)
        
        self._index_built = True
    
    def search(self, query: str, k: int = 10) -> list[dict]:
        """Search using BM25 scoring."""
        if not self._index_built or not self.documents:
            return []
        
        query_terms = self._tokenize(query)
        scores: dict[str, float] = defaultdict(float)
        
        N = len(self.documents)  # total documents
        
        for term in query_terms:
            if term not in self._term_doc_freq:
                continue
            
            df = len(self._term_doc_freq[term])  # document frequency
            idf = self._compute_idf(N, df)
            
            for doc_id, tf in self._term_doc_freq[term].items():
                doc_length = self._doc_lengths[doc_id]
                
                # BM25 score formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_length / self._avg_doc_length)
                )
                
                scores[doc_id] += idf * (numerator / denominator)
        
        # Sort by score and return top k
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        return [
            {
                "id": doc_id,
                "score": score,
                "metadata": self.doc_metadata.get(doc_id, {}),
            }
            for doc_id, score in sorted_docs
        ]
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization: lowercase and split."""
        return text.lower().split()
    
    def _compute_idf(self, N: int, df: int) -> float:
        """Compute IDF (inverse document frequency)."""
        import math
        return math.log((N - df + 0.5) / (df + 0.5) + 1)
    
    def delete(self, ids: list[str]) -> None:
        """Remove documents from index."""
        for doc_id in ids:
            if doc_id in self.documents:
                # Remove from documents
                text = self.documents.pop(doc_id)
                self.doc_metadata.pop(doc_id, None)
                self._doc_lengths.pop(doc_id, None)
                
                # Remove from term index
                terms = self._tokenize(text)
                for term in set(terms):
                    if term in self._term_doc_freq:
                        self._term_doc_freq[term].pop(doc_id, None)
                        if not self._term_doc_freq[term]:
                            del self._term_doc_freq[term]


def reciprocal_rank_fusion(
    result_lists: list[list[dict]], 
    k: int = 60
) -> list[dict]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion (RRF).
    
    RRF score = sum(1 / (k + rank)) across all lists where item appears
    
    Args:
        result_lists: List of ranked result lists from different retrievers
        k: Constant for RRF formula (typically 60)
    
    Returns:
        Merged and re-ranked results
    """
    rrf_scores: dict[str, float] = defaultdict(float)
    doc_metadata: dict[str, dict] = {}
    
    for results in result_lists:
        for rank, result in enumerate(results, start=1):
            doc_id = result["id"]
            rrf_scores[doc_id] += 1.0 / (k + rank)
            
            # Keep metadata from first occurrence
            if doc_id not in doc_metadata:
                doc_metadata[doc_id] = result.get("metadata", {})
    
    # Sort by RRF score
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {
            "id": doc_id,
            "score": score,
            "metadata": doc_metadata.get(doc_id, {}),
        }
        for doc_id, score in sorted_docs
    ]


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


class HybridIndex:
    """Hybrid search combining BM25 (sparse) and dense vector retrieval."""
    
    def __init__(self, collection: str = "signals"):
        self.dense = ChromaIndex(collection)
        self.sparse = BM25Index()
        self.collection = collection
    
    def upsert(self, ids: list[str], texts: list[str], metadata: list[dict]) -> None:
        """Upsert into both indexes."""
        self.dense.upsert(ids, texts, metadata)
        self.sparse.upsert(ids, texts, metadata)
    
    def query(
        self, 
        text: str, 
        k: int = 10, 
        where: dict | None = None,
        hybrid: bool = True,
        alpha: float = 0.5
    ) -> list[dict]:
        """
        Hybrid search combining BM25 and dense retrieval.
        
        Args:
            text: Query text
            k: Number of results
            where: Metadata filters
            hybrid: If True, use hybrid search; if False, dense only
            alpha: Weight for dense vs sparse (0=sparse only, 1=dense only, 0.5=equal)
        
        Returns:
            Ranked results with scores
        """
        if not hybrid or alpha == 1.0:
            # Dense only
            return self.dense.query(text, k=k, where=where)
        
        if alpha == 0.0:
            # Sparse only
            return self.sparse.search(text, k=k * 2)[:k]
        
        # True hybrid: get results from both and fuse
        dense_results = self.dense.query(text, k=k * 2, where=where)
        sparse_results = self.sparse.search(text, k=k * 2)
        
        # Apply RRF fusion
        fused = reciprocal_rank_fusion([dense_results, sparse_results])
        
        # Re-score based on alpha weighting if needed
        # (RRF already does good fusion, but alpha can adjust preference)
        
        return fused[:k]
    
    def delete(self, ids: list[str]) -> None:
        """Delete from both indexes."""
        self.dense.delete(ids)
        self.sparse.delete(ids)


@lru_cache
def get_index(collection: str = "signals", hybrid: bool = True) -> VectorIndex | HybridIndex:
    """
    Get retrieval index.
    
    Args:
        collection: Collection name
        hybrid: If True, return hybrid index; if False, dense only
    
    Returns:
        Index instance
    """
    backend = get_settings().vector_backend.lower()
    if backend == "chroma":
        if hybrid:
            return HybridIndex(collection)
        return ChromaIndex(collection)
    # pgvector implementation slots in here for prod without touching callers.
    raise ValueError(f"Unsupported VECTOR_BACKEND: {backend!r}")
