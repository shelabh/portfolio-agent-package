"""
Minimal query endpoint for the supported SDK path.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from ..models import QueryRequest, QueryResponse
from ...agents import PersonaType
from ...sdk import PortfolioAgent

logger = logging.getLogger(__name__)

router = APIRouter()

CONFIDENCE_BY_EVIDENCE = {
    "strong": 0.9,
    "moderate": 0.75,
    "weak": 0.45,
    "none": 0.2,
}


def get_agent(request: Request) -> PortfolioAgent:
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="PortfolioAgent is not initialized")
    return agent


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest, agent: PortfolioAgent = Depends(get_agent)):
    """Query the indexed corpus through the canonical SDK runtime."""

    start_time = time.time()
    try:
        persona = PersonaType.PROFESSIONAL
        if request.persona and request.persona.lower() in {item.value for item in PersonaType}:
            persona = PersonaType(request.persona.lower())

        result = agent.query(
            request.query,
            session_id=request.session_id or request.user_id or "default",
            persona_type=persona,
            max_documents=request.max_results,
            include_sources=request.include_sources,
            context=request.metadata,
        )
        response_metadata = result.metadata.get("response_metadata", {})
        evidence_strength = response_metadata.get("evidence_strength", "none")
        return QueryResponse(
            response=result.response,
            query_type=request.query_type,
            sources=result.sources,
            confidence=0.0 if result.metadata.get("error") else CONFIDENCE_BY_EVIDENCE.get(evidence_strength, 0.5),
            processing_time=result.processing_time,
            tokens_used=None,
            session_id=result.session_id,
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e}") from e
