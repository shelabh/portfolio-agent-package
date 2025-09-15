"""
Vector stores module for portfolio-agent.

This module provides vector database adapters:
- FAISS (local)
- Pinecone (managed)
- OpenSearch (enterprise)
"""

from .faiss_store import FAISSStore
from .pinecone_store import PineconeStore
from .opensearch_store import OpenSearchStore

__all__ = [
    "FAISSStore",
    "PineconeStore", 
    "OpenSearchStore"
]
