"""Connector registry — maps source name -> connector instance.

Drives both inbound ingestion and the outbound scan loop (`workers/scheduler.py`),
so adding a new source is a one-line registration, not a code change elsewhere.
Connectors are lazily instantiated so that importing the registry never triggers
network clients or API-key checks until a connector is actually used.
"""
from __future__ import annotations

from collections.abc import Callable

from app.memory.ingestion.base import BaseConnector

_FACTORIES: dict[str, Callable[[], BaseConnector]] = {}
_INSTANCES: dict[str, BaseConnector] = {}


def register(name: str, factory: Callable[[], BaseConnector]) -> None:
    _FACTORIES[name] = factory


def get_connector(name: str) -> BaseConnector:
    if name not in _INSTANCES:
        if name not in _FACTORIES:
            raise KeyError(f"No connector registered for source {name!r}")
        _INSTANCES[name] = _FACTORIES[name]()
    return _INSTANCES[name]


def available_sources() -> list[str]:
    return sorted(_FACTORIES)


def _register_builtins() -> None:
    from app.memory.ingestion.arxiv import ArxivConnector
    from app.memory.ingestion.deck_parser import DeckConnector
    from app.memory.ingestion.github import GitHubConnector
    from app.memory.ingestion.producthunt import ProductHuntConnector
    from app.memory.ingestion.tavily import TavilyConnector
    from app.memory.ingestion.web import WebConnector

    register("github", GitHubConnector)
    register("deck", DeckConnector)
    register("arxiv", ArxivConnector)
    register("producthunt", ProductHuntConnector)
    register("tavily", TavilyConnector)
    register("web", WebConnector)


_register_builtins()
