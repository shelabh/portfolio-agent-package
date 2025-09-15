"""
FastAPI Server

This module provides the main FastAPI application with all endpoints,
middleware, and configuration for the Portfolio Agent API.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .endpoints import health, query, documents, agents, metrics, security, admin
from .middleware import (
    RequestLoggingMiddleware,
    SecurityMiddleware,
    RateLimitMiddleware,
    MetricsMiddleware
)
from ..config import settings
from ..rag_pipeline import RAGPipeline
from ..embeddings.openai_embedder import OpenAIEmbedder
from ..vector_stores.faiss_store import FAISSVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for application state
rag_pipeline: RAGPipeline = None
start_time: float = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global rag_pipeline, start_time
    
    # Startup
    logger.info("Starting Portfolio Agent API...")
    start_time = time.time()
    
    try:
        # Initialize RAG pipeline with default agents
        from ..agents import (
            RouterAgent, RetrieverAgent, RerankerAgent, PersonaAgent, MemoryManager
        )
        
        # Initialize components
        embedder = OpenAIEmbedder()
        vector_store = FAISSVectorStore()
        
        # Create agents with required dependencies
        router_agent = RouterAgent()
        retriever_agent = RetrieverAgent(vector_store=vector_store, embedder=embedder)
        reranker_agent = RerankerAgent()
        persona_agent = PersonaAgent()
        memory_manager = MemoryManager()
        
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(
            router_agent=router_agent,
            retriever_agent=retriever_agent,
            reranker_agent=reranker_agent,
            persona_agent=persona_agent,
            memory_manager=memory_manager
        )
        logger.info("RAG pipeline initialized successfully")
        
        logger.info("Portfolio Agent API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Portfolio Agent API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Portfolio Agent API...")
    # Cleanup resources if needed
    logger.info("Portfolio Agent API shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Portfolio Agent API",
        description="A production-ready RAG pipeline with multi-agent architecture",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc", 
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Custom OpenAPI schema
    setup_openapi_schema(app)
    
    return app

def setup_middleware(app: FastAPI) -> None:
    """Setup middleware for the FastAPI application."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MetricsMiddleware)

def setup_routes(app: FastAPI) -> None:
    """Setup API routes."""
    
    # Health and metrics
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
    
    # Core functionality
    app.include_router(query.router, prefix="/api/v1", tags=["query"])
    app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
    app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
    
    # Security
    app.include_router(security.router, prefix="/api/v1", tags=["security"])
    
    # Admin (if not in LOCAL_ONLY mode)
    if not settings.LOCAL_ONLY:
        app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Portfolio Agent API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if not settings.LOCAL_ONLY else "disabled",
            "health": "/api/v1/health"
        }

def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": time.time()
            }
        )

def setup_openapi_schema(app: FastAPI) -> None:
    """Setup custom OpenAPI schema."""
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Portfolio Agent API",
            version="1.0.0",
            description="""
            A production-ready RAG (Retrieval-Augmented Generation) pipeline with multi-agent architecture.
            
            ## Features
            
            - **Multi-Agent Architecture**: Sophisticated pipeline with specialized agents
            - **Document Processing**: Support for multiple document formats with PII redaction
            - **Vector Search**: Advanced similarity search with multiple vector stores
            - **Security**: Built-in security scanning and PII detection
            - **Memory Management**: Conversation context and history tracking
            
            ## Authentication
            
            Most endpoints require authentication. Use the `Authorization` header with a valid API key.
            
            ## Rate Limiting
            
            API requests are rate limited. Check response headers for current limits.
            """,
            routes=app.routes,
        )
        
        # Add security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "API key for authentication"
            }
        }
        
        # Add security requirements
        openapi_schema["security"] = [{"ApiKeyAuth": []}]
        
        # Add server information
        openapi_schema["servers"] = [
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.portfolio-agent.com",
                "description": "Production server"
            }
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi

# Create the app instance
app = create_app()

# Dependency to get RAG pipeline
async def get_rag_pipeline() -> RAGPipeline:
    """Dependency to get the RAG pipeline instance."""
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    return rag_pipeline

# Dependency to get application start time
async def get_start_time() -> float:
    """Dependency to get application start time."""
    return start_time

# Export the app for use in other modules
__all__ = ["app", "create_app", "get_rag_pipeline", "get_start_time"]
