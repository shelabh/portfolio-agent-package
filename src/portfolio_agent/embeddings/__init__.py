"""
Embeddings module for portfolio-agent.

This module provides embedding provider adapters:
- OpenAI embeddings
- Hugging Face sentence-transformers
- Local embedding models
"""

from .openai_embedder import OpenAIEmbedder
from .hf_embedder import HuggingFaceEmbedder

__all__ = [
    "OpenAIEmbedder",
    "HuggingFaceEmbedder"
]
