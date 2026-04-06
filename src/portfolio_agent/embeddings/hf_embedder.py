"""
Hugging Face Embedding Adapter

This module provides an adapter for Hugging Face embedding models,
supporting local inference, batch processing, and GPU acceleration.
"""

import logging
from typing import List, Dict, Any, Optional
import time
from dataclasses import dataclass
import numpy as np

try:
    import torch
except ImportError:
    torch = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    AutoTokenizer = None
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    AutoTokenizer = None
    AutoModel = None
    TRANSFORMERS_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)

KNOWN_EMBEDDING_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "all-mpnet-base-v2": 768,
    "text-embedding-3-small": 1536,
}

@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    embeddings: List[List[float]]
    metadata: Dict[str, Any]
    processing_time: float
    model_used: Optional[str] = None
    device_used: Optional[str] = None

class HuggingFaceEmbedder:
    """Hugging Face embedding adapter with local inference support."""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        use_sentence_transformers: bool = True,
        device: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 512,
        normalize_embeddings: bool = True
    ):
        """Initialize Hugging Face embedder.
        
        Args:
            model_name: Name of the Hugging Face model to use
            use_sentence_transformers: Whether to use sentence-transformers library
            device: Device to run on ('cpu', 'cuda', 'mps', or None for auto)
            batch_size: Number of texts to process in each batch
            max_length: Maximum sequence length for tokenization
            normalize_embeddings: Whether to normalize embeddings to unit vectors
        """
        self.model_name = model_name
        self.use_sentence_transformers = use_sentence_transformers
        self.batch_size = batch_size
        self.max_length = max_length
        self.normalize_embeddings = normalize_embeddings
        self._embedding_dimension: Optional[int] = KNOWN_EMBEDDING_DIMENSIONS.get(model_name)
        
        # Determine device
        if device is None:
            if torch and torch.cuda.is_available():
                self.device = "cuda"
            elif torch and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
        
        # Load model
        self._load_model()
        
        logger.info(f"Initialized Hugging Face embedder with model: {model_name} on {self.device}")
    
    def _load_model(self):
        """Load the embedding model."""
        if self.use_sentence_transformers and not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "The default local embedding path requires `sentence-transformers` and its runtime dependencies. "
                "Install the project dependencies, switch to `EMBEDDING_PROVIDER=openai`, or use the smoke verifier."
            )

        if not self.use_sentence_transformers and not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "The transformers-based embedding path requires `transformers` and `torch`."
            )

        try:
            if self.use_sentence_transformers:
                self.model = SentenceTransformer(self.model_name, device=self.device)
                self.tokenizer = None  # SentenceTransformer handles tokenization
                if hasattr(self.model, "get_sentence_embedding_dimension"):
                    self._embedding_dimension = self.model.get_sentence_embedding_dimension()
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
                hidden_size = getattr(getattr(self.model, "config", None), "hidden_size", None)
                if hidden_size:
                    self._embedding_dimension = int(hidden_size)
                
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise RuntimeError(
                f"Could not load Hugging Face model `{self.model_name}` on device `{self.device}`: {e}. "
                "If this is the first run, the model may still need to be downloaded. "
                "If you want a fast repository check, run `python scripts/manual_e2e.py --mode smoke`."
            )
    
    def embed_texts(
        self,
        texts: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResult:
        """Embed a list of texts using the loaded model.
        
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
                processing_time=0.0,
                model_used=self.model_name,
                device_used=self.device
            )
        
        start_time = time.time()
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
        
        processing_time = time.time() - start_time
        
        result_metadata = {
            **(metadata or {}),
            'total_texts': len(texts),
            'batch_size': self.batch_size,
            'model': self.model_name,
            'device': self.device
        }
        
        return EmbeddingResult(
            embeddings=all_embeddings,
            metadata=result_metadata,
            processing_time=processing_time,
            model_used=self.model_name,
            device_used=self.device
        )
    
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a single batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.use_sentence_transformers:
            return self._embed_batch_sentence_transformers(texts)
        else:
            return self._embed_batch_transformers(texts)
    
    def _embed_batch_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Embed batch using sentence-transformers."""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=len(texts),
                convert_to_tensor=False,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=False
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Sentence transformers embedding failed: {e}")
            raise
    
    def _embed_batch_transformers(self, texts: List[str]) -> List[List[float]]:
        """Embed batch using transformers library."""
        try:
            # Tokenize
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt"
            ).to(self.device)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
                if self.normalize_embeddings:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
                return embeddings.cpu().numpy().tolist()
                
        except Exception as e:
            logger.error(f"Transformers embedding failed: {e}")
            raise
    
    def embed_single(self, text: str) -> List[float]:
        """Embed a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        result = self.embed_texts([text])
        return result.embeddings[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension
        """
        if self._embedding_dimension:
            return int(self._embedding_dimension)

        try:
            # Get dimension by embedding a test text only as a final fallback.
            test_embedding = self.embed_single("test")
            self._embedding_dimension = len(test_embedding)
            return len(test_embedding)
        except Exception as e:
            logger.warning(f"Could not determine embedding dimension: {e}")
            return settings.EMBEDDING_DIMENSION
    
    def health_check(self) -> bool:
        """Check if the model is working correctly.
        
        Returns:
            True if model is working, False otherwise
        """
        try:
            self.embed_single("test")
            return True
        except Exception as e:
            logger.error(f"Hugging Face health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'use_sentence_transformers': self.use_sentence_transformers,
            'embedding_dimension': self.get_embedding_dimension(),
            'batch_size': self.batch_size,
            'max_length': self.max_length,
            'normalize_embeddings': self.normalize_embeddings
        }

# Convenience function for easy access
def create_hf_embedder(**kwargs) -> HuggingFaceEmbedder:
    """Create a Hugging Face embedder with default settings.
    
    Args:
        **kwargs: Arguments to pass to HuggingFaceEmbedder
        
    Returns:
        Configured HuggingFaceEmbedder instance
    """
    return HuggingFaceEmbedder(**kwargs)
