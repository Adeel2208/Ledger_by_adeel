"""Lightweight in-process event bus.

Lets Memory emit e.g. 'signal.ingested' without importing Intelligence, keeping
the dependency direction clean (principle #2). Swap for a real broker later.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

_subscribers: dict[str, list[Callable]] = defaultdict(list)


def subscribe(event: str, handler: Callable) -> None:
    _subscribers[event].append(handler)


def emit(event: str, **payload) -> None:
    for handler in _subscribers.get(event, []):
        handler(**payload)
