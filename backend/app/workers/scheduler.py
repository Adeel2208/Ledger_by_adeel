"""Outbound-scan scheduler (FR-5, D1).

APScheduler runs the outbound scan every OUTBOUND_SCAN_INTERVAL_MIN minutes.
Queue-shaped seam: swap for Celery/BullMQ in the enterprise path without touching
callers.
"""
from __future__ import annotations


def start_scheduler() -> None:
    raise NotImplementedError


def shutdown_scheduler() -> None:
    raise NotImplementedError
