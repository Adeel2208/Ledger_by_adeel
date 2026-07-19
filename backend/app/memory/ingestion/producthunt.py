"""Product launch connector (FR-5): Hacker News 'Show HN' launches as traction signals.

Uses the free HN Algolia API (no key) to find a founder's/product's launch posts —
points + comments are an independent, verifiable traction signal (corroborated tier).
Product Hunt's official API can be slotted in the same way when a token is available.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.memory.ingestion.base import BaseConnector, IngestBundle, RawSignal
from app.schemas.common import Confidence

_HN = "https://hn.algolia.com/api/v1/search"


class ProductHuntConnector(BaseConnector):
    name = "producthunt"

    def fetch(self, *, query: str, max_results: int = 10, **_: Any) -> IngestBundle:
        if not query:
            return IngestBundle(signals=[])
        try:
            resp = httpx.get(
                _HN,
                params={"query": query, "tags": "show_hn", "hitsPerPage": max_results},
                timeout=15,
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            return IngestBundle(signals=[])

        signals: list[RawSignal] = []
        for hit in resp.json().get("hits", []):
            points = hit.get("points") or 0
            signals.append(
                RawSignal(
                    source="producthunt",
                    record_type="product_launch",
                    payload={
                        "title": hit.get("title"),
                        "points": points,
                        "num_comments": hit.get("num_comments"),
                        "url": hit.get("url"),
                    },
                    timestamp=self._parse_ts(hit.get("created_at")),
                    # Community up-votes independently corroborate a launch happened.
                    confidence=Confidence.CORROBORATED,
                    external_url=f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    text=f"Launch: {hit.get('title')} — {points} points, {hit.get('num_comments', 0)} comments",
                )
            )
        return IngestBundle(signals=signals)

    @staticmethod
    def _parse_ts(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
