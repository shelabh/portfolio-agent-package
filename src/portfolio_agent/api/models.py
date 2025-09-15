"""
API Models

This module defines Pydantic models for API request/response schemas.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class QueryType(str, Enum):
    """Types of queries supported by the system."""
    RAG = "rag"
    DIRECT = "direct"
    TOOL = "tool"

class DocumentType(str, Enum):
    """Types of documents supported."""
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JSON = "json"
    DOCX = "docx"

class AgentType(str, Enum):
    """Types of agents available."""
    PERSONA = "persona"
    ROUTER = "router"
    RETRIEVER = "retriever"
    RERANKER = "reranker"
    CRITIC = "critic"
    MEMORY_MANAGER = "memory_manager"

class QueryRequest(BaseModel):
    """Request model for query operations."""
    query: str = Field(..., description="The query text", min_length=1, max_length=1000)
    query_type: QueryType = Field(QueryType.RAG, description="Type of query to process")
    user_id: Optional[str] = Field(None, description="User ID for context and memory")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    max_results: int = Field(5, description="Maximum number of results to return", ge=1, le=20)
    include_sources: bool = Field(True, description="Whether to include source documents")
    persona: Optional[str] = Field(None, description="Persona to use for response generation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()

class QueryResponse(BaseModel):
    """Response model for query operations."""
    response: str = Field(..., description="The generated response")
    query_type: QueryType = Field(..., description="Type of query that was processed")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
    confidence: float = Field(..., description="Confidence score of the response", ge=0.0, le=1.0)
    processing_time: float = Field(..., description="Time taken to process the query in seconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class DocumentRequest(BaseModel):
    """Request model for document operations."""
    content: str = Field(..., description="Document content", min_length=1)
    document_type: DocumentType = Field(..., description="Type of document")
    source: Optional[str] = Field(None, description="Source of the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    chunk_size: int = Field(1000, description="Chunk size for processing", ge=100, le=5000)
    chunk_overlap: int = Field(200, description="Overlap between chunks", ge=0, le=1000)
    redact_pii: bool = Field(True, description="Whether to redact PII from the document")

    @validator('chunk_overlap')
    def validate_chunk_overlap(cls, v, values):
        if 'chunk_size' in values and v >= values['chunk_size']:
            raise ValueError('chunk_overlap must be less than chunk_size')
        return v

class DocumentResponse(BaseModel):
    """Response model for document operations."""
    document_id: str = Field(..., description="Unique identifier for the document")
    chunks_created: int = Field(..., description="Number of chunks created from the document")
    processing_time: float = Field(..., description="Time taken to process the document")
    pii_detected: int = Field(0, description="Number of PII instances detected and redacted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")

class AgentRequest(BaseModel):
    """Request model for agent operations."""
    agent_type: AgentType = Field(..., description="Type of agent to use")
    input_data: Dict[str, Any] = Field(..., description="Input data for the agent")
    user_id: Optional[str] = Field(None, description="User ID for context")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")

class AgentResponse(BaseModel):
    """Response model for agent operations."""
    output: Dict[str, Any] = Field(..., description="Agent output")
    agent_type: AgentType = Field(..., description="Type of agent used")
    processing_time: float = Field(..., description="Time taken to process the request")
    confidence: Optional[float] = Field(None, description="Confidence score", ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the check")
    version: str = Field(..., description="Application version")
    components: Dict[str, str] = Field(..., description="Status of individual components")
    uptime: float = Field(..., description="Application uptime in seconds")

class MetricsResponse(BaseModel):
    """Response model for metrics."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the metrics")
    total_queries: int = Field(..., description="Total number of queries processed")
    total_documents: int = Field(..., description="Total number of documents indexed")
    average_response_time: float = Field(..., description="Average response time in seconds")
    active_sessions: int = Field(..., description="Number of active sessions")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    performance_metrics: Dict[str, float] = Field(..., description="Performance metrics")

class SecurityRequest(BaseModel):
    """Request model for security operations."""
    text: str = Field(..., description="Text to analyze for security", min_length=1)
    check_pii: bool = Field(True, description="Whether to check for PII")
    check_secrets: bool = Field(True, description="Whether to check for secrets")
    check_malicious: bool = Field(True, description="Whether to check for malicious content")

class SecurityResponse(BaseModel):
    """Response model for security operations."""
    is_safe: bool = Field(..., description="Whether the text is safe")
    pii_detected: List[Dict[str, Any]] = Field(default_factory=list, description="PII instances detected")
    secrets_detected: List[Dict[str, Any]] = Field(default_factory=list, description="Secrets detected")
    malicious_content: List[Dict[str, Any]] = Field(default_factory=list, description="Malicious content detected")
    risk_score: float = Field(..., description="Overall risk score", ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")

class AdminRequest(BaseModel):
    """Request model for admin operations."""
    action: str = Field(..., description="Admin action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    admin_key: str = Field(..., description="Admin authentication key")

class AdminResponse(BaseModel):
    """Response model for admin operations."""
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the action")

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the error")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class BatchQueryRequest(BaseModel):
    """Request model for batch query operations."""
    queries: List[QueryRequest] = Field(..., description="List of queries to process", min_items=1, max_items=10)
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    parallel: bool = Field(True, description="Whether to process queries in parallel")

class BatchQueryResponse(BaseModel):
    """Response model for batch query operations."""
    batch_id: str = Field(..., description="Batch identifier")
    results: List[QueryResponse] = Field(..., description="Results for each query")
    total_processing_time: float = Field(..., description="Total time to process all queries")
    success_count: int = Field(..., description="Number of successful queries")
    error_count: int = Field(..., description="Number of failed queries")
    errors: List[ErrorResponse] = Field(default_factory=list, description="Errors encountered")

class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str = Field(..., description="Search query", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    offset: int = Field(0, description="Number of results to skip", ge=0)
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

class SearchResponse(BaseModel):
    """Response model for search operations."""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of matching documents")
    limit: int = Field(..., description="Maximum number of results requested")
    offset: int = Field(..., description="Number of results skipped")
    query_time: float = Field(..., description="Time taken to execute the search")
    facets: Optional[Dict[str, Any]] = Field(None, description="Search facets/aggregations")
