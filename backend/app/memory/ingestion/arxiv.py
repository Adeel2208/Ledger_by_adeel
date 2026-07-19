"""arXiv connector (FR-5): research papers with commercial potential.

Papers authored by an individual are a strong 'deep technical founder' signal and
a valuable cold-start alternate signal (published work without any funding/network).
Uses the public arXiv Atom API — no key required. Confidence is `verified`
(arXiv is an authoritative record of authorship).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from app.memory.ingestion.base import BaseConnector, IngestBundle, RawSignal
from app.schemas.common import Confidence

_API = "http://export.arxiv.org/api/query"


class ArxivConnector(BaseConnector):
    name = "arxiv"

    def fetch(
        self, *, author: str | None = None, query: str | None = None, max_results: int = 10, **_: Any
    ) -> IngestBundle:
        search = f'au:"{author}"' if author else (query or "")
        if not search:
            return IngestBundle(signals=[])

        resp = httpx.get(
            _API,
            params={"search_query": search, "start": 0, "max_results": max_results},
            timeout=20,
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        signals: list[RawSignal] = []
        for entry in feed.entries:
            authors = [a.get("name") for a in entry.get("authors", [])]
            published = entry.get("published", "")
            signals.append(
                RawSignal(
                    source="arxiv",
                    record_type="research_paper",
                    payload={
                        "title": entry.get("title"),
                        "authors": authors,
                        "summary": entry.get("summary"),
                        "published": published,
                        "categories": [t.get("term") for t in entry.get("tags", [])],
                    },
                    timestamp=self._parse_ts(published),
                    confidence=Confidence.VERIFIED,
                    external_url=entry.get("link"),
                    text=f"Paper: {entry.get('title')}. {entry.get('summary', '')[:600]}",
                )
            )

        return IngestBundle(signals=signals, identity={"name": author} if author else {})

    @staticmethod
    def _parse_ts(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
