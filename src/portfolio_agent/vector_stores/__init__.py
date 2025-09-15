"""
Vector Stores Module

This module provides vector store implementations for various backends
including FAISS, Pinecone, OpenSearch, and pgvector.
"""

from .faiss_store import FAISSVectorStore, VectorDocument, SearchResult, create_faiss_store

__all__ = [
    'FAISSVectorStore',
    'VectorDocument', 
    'SearchResult',
    'create_faiss_store'
]
