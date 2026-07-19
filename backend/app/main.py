"""FastAPI application factory.

Wires the Experience-layer routers, cross-cutting middleware, and the background
scheduler. Keep this thin — orchestration belongs in `app/services`, not here.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.services import profile_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch the outbound-sourcing scheduler (APScheduler).
    # from app.workers.scheduler import start_scheduler, shutdown_scheduler
    # start_scheduler()
    yield
    # Shutdown:
    # shutdown_scheduler()


def create_app() -> FastAPI:
    # Read settings inside the factory, not at module import time: importing
    # this module can happen before a host (Railway, etc.) has fully injected
    # its env vars into the process, and get_settings() is lru_cache'd — a
    # premature read here would freeze stale defaults (e.g. CORS_ORIGINS
    # falling back to localhost) for the process's entire lifetime.
    settings = get_settings()

    app = FastAPI(
        title="The VC Brain",
        description="AI deal-flow OS — $100K checks, decision-ready in 24 hours.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    # Serve founder-supplied media (photos). Created eagerly so the mount does
    # not fail on a fresh checkout where nothing has been uploaded yet.
    os.makedirs(profile_service.UPLOAD_DIR, exist_ok=True)
    app.mount("/media", StaticFiles(directory=profile_service.UPLOAD_DIR), name="media")

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
