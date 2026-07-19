"""Generic web / public-footprint connector (FR-11 cold-start).

Blog posts, portfolio sites, YouTube, Stack Overflow, community contributions —
the alternate signals that let cold-start founders be scored fairly. Fetches a
public URL, strips it to text, and lets the LLM extract structured claims.

Web-sourced signals are `scraped` confidence (lowest tier) — public but unverified.
Rate-limited and ethical by design; respects the caller-provided URL only.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.llm.client import get_llm
from app.memory.ingestion.base import BaseConnector, IngestBundle, RawSignal
from app.schemas.common import Confidence
from app.schemas.founder import ExtractedProfile

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

_SYSTEM = (
    "You extract public-footprint signals about a founder from a web page (blog, "
    "portfolio, profile). Capture concrete artifacts (projects shipped, talks, "
    "community contributions, self-taught indicators). Only record what is stated."
)


class WebConnector(BaseConnector):
    name = "web"

    def fetch(self, *, url: str, **_: Any) -> IngestBundle:
        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError:
            return IngestBundle(signals=[])

        text = self._to_text(resp.text)
        if not text:
            return IngestBundle(signals=[])

        profile = get_llm().structured(
            f"Web page ({url}):\n{text[:15000]}",
            ExtractedProfile,
            system=_SYSTEM,
            fast=True,
        )

        now = datetime.now(timezone.utc)
        signals = [
            RawSignal(
                source="web",
                record_type=claim.record_type or "public_footprint",
                payload={"text": claim.text, "value": claim.value, "url": url},
                timestamp=now,
                confidence=Confidence.SCRAPED,
                external_url=url,
                text=claim.text,
            )
            for claim in profile.claims
        ]

        return IngestBundle(
            signals=signals,
            identity={
                "name": profile.founder_name,
                "github_handle": profile.github_handle,
                "linkedin_url": profile.linkedin_url,
            },
        )

    @staticmethod
    def _to_text(html: str) -> str:
        # Drop scripts/styles, strip tags, collapse whitespace. Lightweight on purpose.
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        return _WS_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()
