"""
FAISS Vector Store

This module provides a FAISS-based vector store with persistence,
indexing, similarity search, and metadata filtering.
"""

import os
import json
import pickle
import logging
import inspect
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """A document with its vector representation and metadata."""
    id: str
    content: str
    vector: List[float]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

@dataclass
class SearchResult:
    """Result of a vector search operation."""
    document: VectorDocument
    score: float
    rank: int

class FAISSVectorStore:
    """FAISS-based vector store with persistence and metadata filtering."""
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        dimension: int = 384,
        index_type: str = "flat",
        metric: str = "cosine"
    ):
        """Initialize FAISS vector store.
        
        Args:
            index_path: Path to save/load the FAISS index
            dimension: Dimension of the vectors
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
            metric: Distance metric ('cosine', 'l2', 'ip')
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS library not available. Install with: pip install faiss-cpu or faiss-gpu"
            )
        
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        
        # Initialize index
        self.index = self._create_index()
        self.documents: Dict[str, VectorDocument] = {}
        self.metadata_index: Dict[str, List[str]] = {}  # metadata_value -> document_ids
        
        # Load existing index if it exists
        if os.path.exists(self.index_path):
            self.load()
        
        logger.info(f"Initialized FAISS vector store with {len(self.documents)} documents")
    
    def _create_index(self):
        """Create a new FAISS index."""
        if self.index_type == "flat":
            if self.metric == "cosine":
                # For cosine similarity, we normalize vectors and use inner product
                index = faiss.IndexFlatIP(self.dimension)
            elif self.metric == "l2":
                index = faiss.IndexFlatL2(self.dimension)
            else:
                raise ValueError(f"Unsupported metric for flat index: {self.metric}")
        
        elif self.index_type == "ivf":
            # IVF index for larger datasets
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        
        elif self.index_type == "hnsw":
            # HNSW index for approximate search
            index = faiss.IndexHNSWFlat(self.dimension, 32)
        
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        return index
    
    def add_documents(
        self,
        documents: List[VectorDocument],
        normalize_vectors: bool = True
    ) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            normalize_vectors: Whether to normalize vectors for cosine similarity
            
        Returns:
            List of document IDs that were added
        """
        if not documents:
            return []
        
        added_ids = []
        vectors = []
        
        for doc in documents:
            # Validate vector dimension
            if len(doc.vector) != self.dimension:
                logger.warning(f"Document {doc.id} has wrong dimension: {len(doc.vector)} != {self.dimension}")
                continue
            
            # Normalize vector if needed
            vector = np.array(doc.vector, dtype=np.float32)
            if normalize_vectors and self.metric == "cosine":
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            
            vectors.append(vector)
            self.documents[doc.id] = doc
            added_ids.append(doc.id)
            
            # Update metadata index
            self._update_metadata_index(doc)
        
        if vectors:
            # Add vectors to FAISS index
            vectors_array = np.vstack(vectors)
            self.index.add(vectors_array)
            
            logger.info(f"Added {len(added_ids)} documents to vector store")
        
        return added_ids
    
    def add_texts(
        self,
        texts: List[str],
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add texts with their vectors to the store.
        
        Args:
            texts: List of texts
            vectors: List of corresponding vectors
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs that were added
        """
        if len(texts) != len(vectors):
            raise ValueError("Number of texts must match number of vectors")
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        if ids is None:
            ids = [f"doc_{len(self.documents) + i}" for i in range(len(texts))]
        
        documents = []
        for text, vector, metadata, doc_id in zip(texts, vectors, metadatas, ids):
            doc = VectorDocument(
                id=doc_id,
                content=text,
                vector=vector,
                metadata=metadata,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            documents.append(doc)
        
        return self.add_documents(documents)

    def add_document(
        self,
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Compatibility helper for adding a single document."""
        return self.add_texts(
            texts=[content],
            vectors=[embedding],
            metadatas=[metadata or {}],
            ids=[document_id],
        )
    
    def search(
        self,
        query_vector: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        normalize_vector: bool = True
    ) -> List[SearchResult]:
        """Search for similar documents.
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            filter_metadata: Optional metadata filter
            normalize_vector: Whether to normalize the query vector
            
        Returns:
            List of search results
        """
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector has wrong dimension: {len(query_vector)} != {self.dimension}")
        
        # Normalize query vector if needed
        query_array = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        if normalize_vector and self.metric == "cosine":
            norm = np.linalg.norm(query_array)
            if norm > 0:
                query_array = query_array / norm
        
        # Search in FAISS index
        scores, indices = self.index.search(query_array, min(k * 2, len(self.documents)))
        
        # Convert to search results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            # Get document ID from index
            doc_id = list(self.documents.keys())[idx]
            document = self.documents[doc_id]
            
            # Apply metadata filter if provided
            if filter_metadata and not self._matches_filter(document, filter_metadata):
                continue
            
            # Convert score based on metric
            if self.metric == "cosine":
                # FAISS returns inner product for cosine similarity
                final_score = float(score)
            else:
                # For L2 distance, lower is better
                final_score = 1.0 / (1.0 + float(score))
            
            result = SearchResult(
                document=document,
                score=final_score,
                rank=len(results) + 1
            )
            results.append(result)
            
            if len(results) >= k:
                break
        
        return results
    
    def search_by_text(
        self,
        text: str,
        embedder,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search using text query (requires embedder).
        
        Args:
            text: Query text
            embedder: Embedding model to convert text to vector
            k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results
        """
        # Get embedding for the text
        if hasattr(embedder, 'embed_single_sync'):
            query_vector = embedder.embed_single_sync(text)
        elif hasattr(embedder, 'embed_single'):
            query_vector = embedder.embed_single(text)
            if inspect.isawaitable(query_vector):
                raise RuntimeError(
                    "The configured embedder only exposes an async query API. "
                    "Use an embedder with embed_single_sync for the supported runtime."
                )
        else:
            # Assume it's a function
            query_vector = embedder(text)
        
        return self.search(query_vector, k, filter_metadata)

    def is_initialized(self) -> bool:
        """Return whether the vector store is ready for reads/writes."""
        return self.index is not None
    
    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if doc_id not in self.documents:
            return False
        
        # Remove from documents
        document = self.documents.pop(doc_id)
        
        # Remove from metadata index
        self._remove_from_metadata_index(document)
        
        # Note: FAISS doesn't support deletion, so we need to rebuild the index
        # For now, we'll just mark it as deleted in our documents dict
        logger.warning("FAISS doesn't support deletion. Consider rebuilding the index.")
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_documents': len(self.documents),
            'index_type': self.index_type,
            'dimension': self.dimension,
            'metric': self.metric,
            'index_size': self.index.ntotal if hasattr(self.index, 'ntotal') else len(self.documents)
        }
    
    def save(self, path: Optional[str] = None):
        """Save the vector store to disk.
        
        Args:
            path: Optional path to save to (uses self.index_path if None)
        """
        save_path = path or self.index_path
        
        # Create directory if it doesn't exist
        save_dir = os.path.dirname(save_path)
        if save_dir:  # Only create directory if there's a directory path
            os.makedirs(save_dir, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{save_path}.faiss")
        
        # Save documents and metadata
        with open(f"{save_path}.pkl", "wb") as f:
            pickle.dump({
                'documents': self.documents,
                'metadata_index': self.metadata_index,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'metric': self.metric
            }, f)
        
        logger.info(f"Saved vector store to {save_path}")
    
    def load(self, path: Optional[str] = None):
        """Load the vector store from disk.
        
        Args:
            path: Optional path to load from (uses self.index_path if None)
        """
        load_path = path or self.index_path
        
        if not os.path.exists(f"{load_path}.faiss"):
            logger.warning(f"FAISS index file not found: {load_path}.faiss")
            return
        
        if not os.path.exists(f"{load_path}.pkl"):
            logger.warning(f"Documents file not found: {load_path}.pkl")
            return
        
        try:
            # Load FAISS index
            loaded_index = faiss.read_index(f"{load_path}.faiss")
            
            # Load documents and metadata
            with open(f"{load_path}.pkl", "rb") as f:
                data = pickle.load(f)
                loaded_documents = data['documents']
                loaded_metadata_index = data.get('metadata_index', {})
                stored_dimension = data.get('dimension', self.dimension)
                stored_index_type = data.get('index_type', self.index_type)
                stored_metric = data.get('metric', self.metric)

            index_dimension = getattr(loaded_index, 'd', stored_dimension)
            if stored_dimension != self.dimension or index_dimension != self.dimension:
                raise ValueError(
                    "Stored FAISS index is incompatible with the configured embedder dimension. "
                    f"Expected {self.dimension}, found stored={stored_dimension}, index={index_dimension}. "
                    "Use a different FAISS_INDEX_PATH or remove the old index files."
                )

            if stored_index_type != self.index_type or stored_metric != self.metric:
                raise ValueError(
                    "Stored FAISS index settings do not match the configured runtime. "
                    f"Expected ({self.index_type}, {self.metric}), found ({stored_index_type}, {stored_metric}). "
                    "Use a different FAISS_INDEX_PATH or remove the old index files."
                )

            if hasattr(loaded_index, 'ntotal') and loaded_index.ntotal != len(loaded_documents):
                raise ValueError(
                    "Stored FAISS index and document metadata are out of sync. "
                    f"Index contains {loaded_index.ntotal} vectors but metadata has {len(loaded_documents)} documents. "
                    "Use a different FAISS_INDEX_PATH or remove the old index files."
                )

            self.index = loaded_index
            self.documents = loaded_documents
            self.metadata_index = loaded_metadata_index
            self.dimension = stored_dimension
            self.index_type = stored_index_type
            self.metric = stored_metric
            
            logger.info(f"Loaded vector store from {load_path} with {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            raise
    
    def _update_metadata_index(self, document: VectorDocument):
        """Update the metadata index for a document."""
        for key, value in document.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                metadata_key = f"{key}:{value}"
                if metadata_key not in self.metadata_index:
                    self.metadata_index[metadata_key] = []
                if document.id not in self.metadata_index[metadata_key]:
                    self.metadata_index[metadata_key].append(document.id)
    
    def _remove_from_metadata_index(self, document: VectorDocument):
        """Remove a document from the metadata index."""
        for key, value in document.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                metadata_key = f"{key}:{value}"
                if metadata_key in self.metadata_index:
                    if document.id in self.metadata_index[metadata_key]:
                        self.metadata_index[metadata_key].remove(document.id)
    
    def _matches_filter(self, document: VectorDocument, filter_metadata: Dict[str, Any]) -> bool:
        """Check if a document matches the metadata filter."""
        for key, value in filter_metadata.items():
            if key not in document.metadata:
                return False
            if document.metadata[key] != value:
                return False
        return True

# Convenience function for easy access
def create_faiss_store(**kwargs) -> FAISSVectorStore:
    """Create a FAISS vector store with default settings.
    
    Args:
        **kwargs: Arguments to pass to FAISSVectorStore
        
    Returns:
        Configured FAISSVectorStore instance
    """
    return FAISSVectorStore(**kwargs)
