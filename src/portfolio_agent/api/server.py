"""
Supported FastAPI wrapper around the canonical PortfolioAgent SDK.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import documents, health, query
from .. import __version__
from ..config import settings
from ..sdk import PortfolioAgent

logger = logging.getLogger(__name__)


def _build_agent() -> PortfolioAgent:
    return PortfolioAgent.from_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = time.time()
    if getattr(app.state, "agent", None) is None:
        app.state.agent = _build_agent()
    logger.info("Portfolio Agent API started")
    yield
    logger.info("Portfolio Agent API stopped")


def create_app(agent: Optional[PortfolioAgent] = None) -> FastAPI:
    """Create the supported FastAPI application."""

    app = FastAPI(
        title="Portfolio Agent API",
        description="Thin HTTP wrapper around the supported PortfolioAgent SDK",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.agent = agent
    app.state.started_at = time.time()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(query.router, prefix="/api/v1", tags=["query"])
    app.include_router(documents.router, prefix="/api/v1", tags=["documents"])

    @app.get("/")
    async def root():
        return {
            "name": "portfolio-agent",
            "version": __version__,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app


app = create_app()
