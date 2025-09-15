"""
API Module

This module provides the FastAPI-based REST API for the Portfolio Agent,
including endpoints for RAG operations, document management, and agent interactions.
"""

from .server import app, create_app
from .models import (
    QueryRequest, QueryResponse, DocumentRequest, DocumentResponse,
    HealthResponse, MetricsResponse, AgentRequest, AgentResponse
)
from .endpoints import (
    health, query, documents, agents, metrics, security, admin
)

__all__ = [
    'app',
    'create_app',
    'QueryRequest',
    'QueryResponse', 
    'DocumentRequest',
    'DocumentResponse',
    'HealthResponse',
    'MetricsResponse',
    'AgentRequest',
    'AgentResponse',
    'health',
    'query',
    'documents',
    'agents',
    'metrics',
    'security',
    'admin'
]
