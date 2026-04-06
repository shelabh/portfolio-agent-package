"""
Vector Stores Module

This module exposes the supported local FAISS vector store used by the
canonical PortfolioAgent SDK path.
"""

from .faiss_store import FAISSVectorStore, VectorDocument, SearchResult, create_faiss_store

__all__ = [
    'FAISSVectorStore',
    'VectorDocument', 
    'SearchResult',
    'create_faiss_store'
]
