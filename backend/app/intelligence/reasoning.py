"""Multi-attribute reasoning (FR-3).

Turn a compound NL query into a structured filter + semantic query in a single
pass, then rank and explain results. e.g. "technical founder, Berlin, AI infra,
enterprise traction, no prior VC backing, top-tier accelerator".
"""
from __future__ import annotations


def resolve_query(natural_language: str) -> dict:
    raise NotImplementedError
