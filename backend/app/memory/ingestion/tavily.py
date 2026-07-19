"""Tavily web-search connector — real external enrichment & corroboration.

Tavily aggregates and ranks live web results, which we use to:
  - enrich a founder/company with an external footprint,
  - give the Market axis real market/competitor context,
  - provide INDEPENDENT sources that can corroborate (or contradict) deck claims.

The synthesized `answer` is tagged `corroborated` (multi-source synthesis); each
individual result is `scraped` (single unverified page). Provenance (URL) is kept
for evidence tracing. No key -> returns an empty bundle (graceful degradation).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.memory.ingestion.base import BaseConnector, IngestBundle, RawSignal
from app.schemas.common import Confidence

_ENDPOINT = "https://api.tavily.com/search"


class TavilyConnector(BaseConnector):
    name = "tavily"

    def __init__(self) -> None:
        self._key = get_settings().tavily_api_key

    def fetch(
        self, *, query: str, max_results: int = 5, topic: str = "general", **_: Any
    ) -> IngestBundle:
        if not self._key or not query:
            return IngestBundle(signals=[])

        try:
            resp = httpx.post(
                _ENDPOINT,
                json={
                    "api_key": self._key,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "max_results": max_results,
                    "topic": topic,
                },
                timeout=30,
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            return IngestBundle(signals=[])

        data = resp.json()
        now = datetime.now(timezone.utc)
        signals: list[RawSignal] = []

        answer = data.get("answer")
        if answer:
            signals.append(
                RawSignal(
                    source="tavily",
                    record_type="web_synthesis",
                    payload={"text": answer, "query": query},
                    timestamp=now,
                    confidence=Confidence.CORROBORATED,
                    external_url=None,
                    text=answer,
                )
            )

        for r in data.get("results", []):
            signals.append(
                RawSignal(
                    source="tavily",
                    record_type="web_result",
                    payload={
                        "title": r.get("title"),
                        "content": r.get("content"),
                        "url": r.get("url"),
                        "relevance": r.get("score"),
                    },
                    timestamp=now,
                    confidence=Confidence.SCRAPED,
                    external_url=r.get("url"),
                    text=f"{r.get('title')}: {r.get('content', '')[:500]}",
                )
            )

        return IngestBundle(signals=signals)

    # Direct helper for the validator agent (returns Tavily's synthesized answer).
    def answer(self, query: str) -> str | None:
        bundle = self.fetch(query=query, max_results=5)
        for s in bundle.signals:
            if s.record_type == "web_synthesis":
                return s.text
        return None
