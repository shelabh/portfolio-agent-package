"""
Embeddings Module

This module provides embedding adapters for various providers including
OpenAI and Hugging Face models.
"""

from .openai_embedder import OpenAIEmbedder, create_openai_embedder
from .hf_embedder import HuggingFaceEmbedder, create_hf_embedder

__all__ = [
    'OpenAIEmbedder',
    'create_openai_embedder',
    'HuggingFaceEmbedder', 
    'create_hf_embedder'
]