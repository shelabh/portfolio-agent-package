"""Pydantic models for the supported HTTP wrapper."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

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

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
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

    @model_validator(mode='after')
    def validate_chunk_overlap(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError('chunk_overlap must be less than chunk_size')
        return self

class DocumentResponse(BaseModel):
    """Response model for document operations."""
    document_id: str = Field(..., description="Unique identifier for the document")
    chunks_created: int = Field(..., description="Number of chunks created from the document")
    processing_time: float = Field(..., description="Time taken to process the document")
    pii_detected: int = Field(0, description="Number of PII instances detected and redacted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")

class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the check")
    version: str = Field(..., description="Application version")
    components: Dict[str, str] = Field(..., description="Status of individual components")
    uptime: float = Field(..., description="Application uptime in seconds")
