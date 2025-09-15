"""
Health Check Endpoints

This module provides health check and readiness endpoints for the API.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..models import HealthResponse
# Removed circular import - will use time.time() directly
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the application and its components.
    """
    try:
        uptime = 0  # Simplified for demo
        
        # Check component health
        components = await _check_components()
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in components.values()
        ) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            version="1.0.0",
            components=components,
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")

@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns whether the application is ready to serve requests.
    """
    try:
        # Check if all critical components are ready
        components = await _check_components()
        
        # Application is ready if all critical components are healthy
        critical_components = ["database", "vector_store", "embedder"]
        is_ready = all(
            components.get(component) == "healthy" 
            for component in critical_components
        )
        
        if is_ready:
            return {"status": "ready", "timestamp": datetime.now().isoformat()}
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat(),
                    "components": components
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Returns whether the application is alive (basic process check).
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "pid": os.getpid() if hasattr(os, 'getpid') else None
    }

async def _check_components() -> Dict[str, str]:
    """Check the health of individual components."""
    components = {}
    
    try:
        # Check database connection
        components["database"] = await _check_database()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        components["database"] = "unhealthy"
    
    try:
        # Check vector store
        components["vector_store"] = await _check_vector_store()
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        components["vector_store"] = "unhealthy"
    
    try:
        # Check embedder
        components["embedder"] = await _check_embedder()
    except Exception as e:
        logger.error(f"Embedder health check failed: {e}")
        components["embedder"] = "unhealthy"
    
    try:
        # Check LLM client
        components["llm_client"] = await _check_llm_client()
    except Exception as e:
        logger.error(f"LLM client health check failed: {e}")
        components["llm_client"] = "unhealthy"
    
    try:
        # Check Redis (if configured)
        components["redis"] = await _check_redis()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        components["redis"] = "unhealthy"
    
    return components

async def _check_database() -> str:
    """Check database connectivity."""
    try:
        # Import here to avoid circular imports
        from ...utils import get_database_connection
        
        if settings.DATABASE_URL:
            conn = get_database_connection()
            if conn:
                # Simple query to test connection
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                return "healthy"
            else:
                return "unhealthy"
        else:
            return "not_configured"
            
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return "unhealthy"

async def _check_vector_store() -> str:
    """Check vector store connectivity."""
    try:
        from ...vector_stores.faiss_store import FAISSVectorStore
        
        store = FAISSVectorStore()
        if store.is_initialized():
            return "healthy"
        else:
            return "not_initialized"
            
    except Exception as e:
        logger.error(f"Vector store check failed: {e}")
        return "unhealthy"

async def _check_embedder() -> str:
    """Check embedder functionality."""
    try:
        from ...embeddings.openai_embedder import OpenAIEmbedder
        
        if settings.OPENAI_API_KEY:
            embedder = OpenAIEmbedder()
            # Test with a simple embedding
            result = await embedder.embed_texts(["test"])
            if result and len(result.embeddings) > 0:
                return "healthy"
            else:
                return "unhealthy"
        else:
            return "not_configured"
            
    except Exception as e:
        logger.error(f"Embedder check failed: {e}")
        return "unhealthy"

async def _check_llm_client() -> str:
    """Check LLM client connectivity."""
    try:
        if settings.OPENAI_API_KEY:
            # Simple test - just check if API key is configured
            return "configured"
        else:
            return "not_configured"
            
    except Exception as e:
        logger.error(f"LLM client check failed: {e}")
        return "unhealthy"

async def _check_redis() -> str:
    """Check Redis connectivity."""
    try:
        if settings.REDIS_URL:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            return "healthy"
        else:
            return "not_configured"
            
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        return "unhealthy"
