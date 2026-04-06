"""
Truthful health endpoints for the supported app surface.
"""

import time
from datetime import datetime

from fastapi import APIRouter, Request

from ..models import HealthResponse
from ... import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    started_at = getattr(request.app.state, "started_at", time.time())
    agent_ready = getattr(request.app.state, "agent", None) is not None
    return HealthResponse(
        status="healthy" if agent_ready else "starting",
        version=__version__,
        components={"portfolio_agent": "healthy" if agent_ready else "starting"},
        uptime=time.time() - started_at,
    )


@router.get("/ready")
async def readiness_check(request: Request):
    ready = getattr(request.app.state, "agent", None) is not None
    return {
        "status": "ready" if ready else "starting",
        "timestamp": datetime.now().isoformat(),
    }
