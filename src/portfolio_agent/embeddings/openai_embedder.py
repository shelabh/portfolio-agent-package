"""
OpenAI Embedding Adapter

This module provides an adapter for OpenAI's embedding API, supporting
batch processing, error handling, and rate limiting.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
import time
from dataclasses import dataclass

try:
    import openai
    from openai import AsyncOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    AsyncOpenAI = None
    OpenAI = None

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    embeddings: List[List[float]]
    metadata: Dict[str, Any]
    processing_time: float
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None

class OpenAIEmbedder:
    """OpenAI embedding adapter with batch processing and error handling."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        max_retries: int = 3,
        rate_limit_delay: float = 0.1
    ):
        """Initialize OpenAI embedder.
        
        Args:
            api_key: OpenAI API key. If None, uses settings.OPENAI_API_KEY
            model: Embedding model to use
            batch_size: Number of texts to process in each batch
            max_retries: Maximum number of retry attempts
            rate_limit_delay: Delay between requests to respect rate limits
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not available. Install with: pip install openai"
            )
        
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.sync_client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI embedder with model: {model}")
    
    async def embed_texts(
        self,
        texts: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResult:
        """Embed a list of texts using OpenAI's API.
        
        Args:
            texts: List of texts to embed
            metadata: Optional metadata to include in result
            
        Returns:
            EmbeddingResult with embeddings and metadata
        """
        if not texts:
            return EmbeddingResult(
                embeddings=[],
                metadata=metadata or {},
                processing_time=0.0
            )
        
        start_time = time.time()
        all_embeddings = []
        total_tokens = 0
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings, batch_tokens = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            total_tokens += batch_tokens
            
            # Rate limiting
            if i + self.batch_size < len(texts):
                await asyncio.sleep(self.rate_limit_delay)
        
        processing_time = time.time() - start_time
        
        result_metadata = {
            **(metadata or {}),
            'total_texts': len(texts),
            'batch_size': self.batch_size,
            'model': self.model
        }
        
        return EmbeddingResult(
            embeddings=all_embeddings,
            metadata=result_metadata,
            processing_time=processing_time,
            tokens_used=total_tokens,
            model_used=self.model
        )
    
    async def _embed_batch(self, texts: List[str]) -> tuple[List[List[float]], int]:
        """Embed a single batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Tuple of (embeddings, tokens_used)
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                embeddings = [data.embedding for data in response.data]
                tokens_used = response.usage.total_tokens
                
                return embeddings, tokens_used
                
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to embed texts after {self.max_retries} attempts: {e}")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

    def embed_texts_sync(
        self,
        texts: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResult:
        """Synchronous embedding API for the supported SDK runtime."""
        if not texts:
            return EmbeddingResult(embeddings=[], metadata=metadata or {}, processing_time=0.0)

        start_time = time.time()
        all_embeddings = []
        total_tokens = 0

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings, batch_tokens = self._embed_batch_sync(batch)
            all_embeddings.extend(batch_embeddings)
            total_tokens += batch_tokens
            if i + self.batch_size < len(texts):
                time.sleep(self.rate_limit_delay)

        processing_time = time.time() - start_time
        result_metadata = {
            **(metadata or {}),
            "total_texts": len(texts),
            "batch_size": self.batch_size,
            "model": self.model,
        }
        return EmbeddingResult(
            embeddings=all_embeddings,
            metadata=result_metadata,
            processing_time=processing_time,
            tokens_used=total_tokens,
            model_used=self.model,
        )

    def _embed_batch_sync(self, texts: List[str]) -> tuple[List[List[float]], int]:
        for attempt in range(self.max_retries):
            try:
                response = self.sync_client.embeddings.create(model=self.model, input=texts)
                embeddings = [data.embedding for data in response.data]
                tokens_used = response.usage.total_tokens
                return embeddings, tokens_used
            except Exception as e:
                logger.warning(f"Sync embedding attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to embed texts after {self.max_retries} attempts: {e}")
                time.sleep(2 ** attempt)

    def embed_single_sync(self, text: str) -> List[float]:
        """Embed a single text synchronously."""
        result = self.embed_texts_sync([text])
        return result.embeddings[0]
    
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        result = await self.embed_texts([text])
        return result.embeddings[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension
        """
        # Common OpenAI embedding dimensions
        dimension_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        return dimension_map.get(self.model, 1536)
    
    async def health_check(self) -> bool:
        """Check if the OpenAI API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            await self.embed_single("test")
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False

# Convenience function for easy access
def create_openai_embedder(**kwargs) -> OpenAIEmbedder:
    """Create an OpenAI embedder with default settings.
    
    Args:
        **kwargs: Arguments to pass to OpenAIEmbedder
        
    Returns:
        Configured OpenAIEmbedder instance
    """
    return OpenAIEmbedder(**kwargs)
