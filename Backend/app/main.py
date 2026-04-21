"""
app/main.py
────────────
FastAPI application factory.
Registers all routers, configures CORS, lifespan startup/shutdown,
and global exception handlers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)
_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown hooks."""
    log.info(
        "swarm_starting",
        env=_settings.APP_ENV,
        debug=_settings.APP_DEBUG,
    )
    # Pre-compile the LangGraph graph on startup (avoids cold-start on first request)
    from app.agents.graph import get_compiled_graph
    get_compiled_graph()
    log.info("langgraph_compiled_on_startup")

    yield  # ── Application running ──────────────────────────────────────────

    log.info("swarm_shutting_down")
    from app.database.session import engine
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Adversarial Swarm — Market Intelligence API",
        description="Multi-agent AI system for market movement prediction",
        version="1.0.0",
        docs_url="/docs" if not _settings.is_production else None,
        redoc_url="/redoc" if not _settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.api.v1.router import v1_router
    from app.api.v1.ws import ws_router
    app.include_router(v1_router)
    app.include_router(ws_router)

    # ── Global exception handlers ─────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred"},
        )

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "env": _settings.APP_ENV}

    return app


app = create_app()
