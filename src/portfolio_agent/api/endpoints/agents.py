"""
Agent Endpoints

This module provides endpoints for interacting with individual agents.
"""

import time
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from ..models import AgentRequest, AgentResponse, AgentType
# Removed circular import - will create RAG pipeline locally
from ...rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_rag_pipeline() -> RAGPipeline:
    """Get RAG pipeline instance."""
    # Import the global RAG pipeline from server
    from ..server import rag_pipeline
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check server logs."
        )
    return rag_pipeline

@router.post("/agents/{agent_type}", response_model=AgentResponse)
async def execute_agent(
    agent_type: AgentType,
    request: AgentRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Execute a specific agent with input data.
    
    This endpoint allows direct interaction with individual agents in the pipeline.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Executing agent: {agent_type}")
        
        # Execute the agent
        result = await rag_pipeline.execute_agent(
            agent_type=agent_type.value,
            input_data=request.input_data,
            user_id=request.user_id,
            session_id=request.session_id,
            config=request.config
        )
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            output=result.get('output', {}),
            agent_type=agent_type,
            processing_time=processing_time,
            confidence=result.get('confidence'),
            metadata=result.get('metadata', {})
        )
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )

@router.get("/agents/{agent_type}/status")
async def get_agent_status(
    agent_type: AgentType,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get the status of a specific agent.
    
    This endpoint returns the current status and configuration of an agent.
    """
    try:
        status = await rag_pipeline.get_agent_status(agent_type.value)
        
        return {
            "agent_type": agent_type,
            "status": status.get('status', 'unknown'),
            "config": status.get('config', {}),
            "metrics": status.get('metrics', {}),
            "last_updated": status.get('last_updated')
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )

@router.post("/agents/{agent_type}/configure")
async def configure_agent(
    agent_type: AgentType,
    config: Dict[str, Any],
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Configure a specific agent.
    
    This endpoint allows updating the configuration of an agent.
    """
    try:
        success = await rag_pipeline.configure_agent(
            agent_type=agent_type.value,
            config=config
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to configure agent")
        
        return {
            "message": f"Agent {agent_type} configured successfully",
            "config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure agent: {str(e)}"
        )
