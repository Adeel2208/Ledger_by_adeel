"""Shared enums / value objects used across schemas.

`Confidence` is the reliability tier attached to every signal and evidence link.
The ordering is meaningful: verified > corroborated > claimed > scraped.
"""
from __future__ import annotations

from enum import Enum


class Confidence(str, Enum):
    VERIFIED = "verified"          # independently confirmed (API, official record)
    CORROBORATED = "corroborated"  # 2+ independent sources agree
    CLAIMED = "claimed"            # founder-asserted only (e.g. deck)
    SCRAPED = "scraped"            # public web, unverified

    @property
    def rank(self) -> int:
        return {"verified": 3, "corroborated": 2, "claimed": 1, "scraped": 0}[self.value]


class SourceType(str, Enum):
    GITHUB = "github"
    DECK = "deck"
    ARXIV = "arxiv"
    PRODUCTHUNT = "producthunt"
    WEB = "web"
    MANUAL = "manual"
