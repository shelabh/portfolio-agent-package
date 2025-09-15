"""
Retriever Agent for portfolio-agent.

This module provides document retrieval functionality from vector stores
with configurable search parameters and result filtering.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetrievalRequest:
    """Request for document retrieval."""
    query: str
    k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None
    min_score: float = 0.0
    include_metadata: bool = True

@dataclass
class RetrievalResult:
    """Result of document retrieval."""
    documents: List[Dict[str, Any]]
    query: str
    total_found: int
    retrieval_time: float
    metadata: Dict[str, Any]

class RetrieverAgent:
    """Retriever agent for document retrieval from vector stores."""
    
    def __init__(
        self,
        vector_store,
        embedder,
        default_k: int = 5,
        min_score_threshold: float = 0.0,
        max_retrieval_time: float = 10.0
    ):
        """Initialize retriever agent.
        
        Args:
            vector_store: Vector store instance for document retrieval
            embedder: Embedding model for query vectorization
            default_k: Default number of documents to retrieve
            min_score_threshold: Minimum similarity score threshold
            max_retrieval_time: Maximum time allowed for retrieval
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.default_k = default_k
        self.min_score_threshold = min_score_threshold
        self.max_retrieval_time = max_retrieval_time
        
        logger.info("Retriever agent initialized")
    
    def retrieve_documents(
        self,
        request: RetrievalRequest,
        context: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """Retrieve documents based on the request.
        
        Args:
            request: Retrieval request with query and parameters
            context: Optional context information
            
        Returns:
            RetrievalResult with retrieved documents
        """
        import time
        start_time = time.time()
        
        logger.info(f"Retrieving documents for query: {request.query[:100]}...")
        
        try:
            # Perform vector search
            search_results = self.vector_store.search_by_text(
                text=request.query,
                embedder=self.embedder,
                k=request.k,
                filter_metadata=request.filter_metadata
            )
            
            # Filter results by score
            filtered_results = [
                result for result in search_results
                if result.score >= max(request.min_score, self.min_score_threshold)
            ]
            
            # Convert to document format
            documents = []
            for result in filtered_results:
                doc = {
                    "id": result.document.id,
                    "content": result.document.content,
                    "score": result.score,
                    "rank": result.rank
                }
                
                if request.include_metadata:
                    doc["metadata"] = result.document.metadata
                
                documents.append(doc)
            
            retrieval_time = time.time() - start_time
            
            # Create result
            result = RetrievalResult(
                documents=documents,
                query=request.query,
                total_found=len(documents),
                retrieval_time=retrieval_time,
                metadata={
                    "k_requested": request.k,
                    "min_score_used": max(request.min_score, self.min_score_threshold),
                    "filter_applied": request.filter_metadata is not None,
                    "context_provided": context is not None
                }
            )
            
            logger.info(f"Retrieved {len(documents)} documents in {retrieval_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error during document retrieval: {e}")
            # Return empty result on error
            return RetrievalResult(
                documents=[],
                query=request.query,
                total_found=0,
                retrieval_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def retrieve_similar_documents(
        self,
        document_id: str,
        k: int = 5,
        min_score: float = 0.0
    ) -> RetrievalResult:
        """Retrieve documents similar to a given document.
        
        Args:
            document_id: ID of the reference document
            k: Number of similar documents to retrieve
            min_score: Minimum similarity score
            
        Returns:
            RetrievalResult with similar documents
        """
        import time
        start_time = time.time()
        
        logger.info(f"Retrieving documents similar to: {document_id}")
        
        try:
            # Get the reference document
            ref_doc = self.vector_store.get_document(document_id)
            if not ref_doc:
                logger.warning(f"Document not found: {document_id}")
                return RetrievalResult(
                    documents=[],
                    query=f"similar_to_{document_id}",
                    total_found=0,
                    retrieval_time=time.time() - start_time,
                    metadata={"error": "Reference document not found"}
                )
            
            # Search using the document's vector
            search_results = self.vector_store.search(
                query_vector=ref_doc.vector,
                k=k + 1,  # +1 to account for the reference document itself
                filter_metadata=None,
                normalize_vector=False
            )
            
            # Filter out the reference document and by score
            filtered_results = [
                result for result in search_results
                if result.document.id != document_id and result.score >= min_score
            ]
            
            # Convert to document format
            documents = []
            for result in filtered_results[:k]:  # Limit to requested k
                doc = {
                    "id": result.document.id,
                    "content": result.document.content,
                    "score": result.score,
                    "rank": result.rank,
                    "metadata": result.document.metadata
                }
                documents.append(doc)
            
            retrieval_time = time.time() - start_time
            
            result = RetrievalResult(
                documents=documents,
                query=f"similar_to_{document_id}",
                total_found=len(documents),
                retrieval_time=retrieval_time,
                metadata={
                    "reference_document": document_id,
                    "k_requested": k,
                    "min_score_used": min_score
                }
            )
            
            logger.info(f"Retrieved {len(documents)} similar documents in {retrieval_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error during similar document retrieval: {e}")
            return RetrievalResult(
                documents=[],
                query=f"similar_to_{document_id}",
                total_found=0,
                retrieval_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            doc = self.vector_store.get_document(document_id)
            if doc:
                return {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics.
        
        Returns:
            Dictionary with retrieval statistics
        """
        try:
            store_stats = self.vector_store.get_stats()
            return {
                "vector_store_stats": store_stats,
                "default_k": self.default_k,
                "min_score_threshold": self.min_score_threshold,
                "max_retrieval_time": self.max_retrieval_time,
                "embedder_info": getattr(self.embedder, 'get_model_info', lambda: {})()
            }
        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {"error": str(e)}

# Convenience function for easy access
def create_retriever_agent(vector_store, embedder, **kwargs) -> RetrieverAgent:
    """Create a retriever agent with default settings.
    
    Args:
        vector_store: Vector store instance
        embedder: Embedding model
        **kwargs: Additional arguments to pass to RetrieverAgent
        
    Returns:
        Configured RetrieverAgent instance
    """
    return RetrieverAgent(vector_store, embedder, **kwargs)