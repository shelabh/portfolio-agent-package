"""
Reranker Agent for portfolio-agent.

This module provides result reranking functionality to improve the quality
of retrieved documents based on various ranking criteria.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..text_matching import extract_terms, keyword_overlap

logger = logging.getLogger(__name__)

class RerankingStrategy(Enum):
    """Available reranking strategies."""
    SCORE_ONLY = "score_only"
    KEYWORD_MATCH = "keyword_match"
    RECENCY = "recency"
    RELEVANCE = "relevance"
    HYBRID = "hybrid"

@dataclass
class RerankingRequest:
    """Request for document reranking."""
    documents: List[Dict[str, Any]]
    query: str
    strategy: RerankingStrategy = RerankingStrategy.HYBRID
    max_results: int = 5
    min_score: float = 0.0
    context: Optional[Dict[str, Any]] = None

@dataclass
class RerankingResult:
    """Result of document reranking."""
    documents: List[Dict[str, Any]]
    original_count: int
    reranked_count: int
    reranking_time: float
    strategy_used: RerankingStrategy
    metadata: Dict[str, Any]

class RerankerAgent:
    """Reranker agent for improving document ranking quality."""
    
    def __init__(
        self,
        default_strategy: RerankingStrategy = RerankingStrategy.HYBRID,
        max_reranking_time: float = 5.0
    ):
        """Initialize reranker agent.
        
        Args:
            default_strategy: Default reranking strategy to use
            max_reranking_time: Maximum time allowed for reranking
        """
        self.default_strategy = default_strategy
        self.max_reranking_time = max_reranking_time
        
        # Define reranking strategies
        self.strategies = {
            RerankingStrategy.SCORE_ONLY: self._score_only_rerank,
            RerankingStrategy.KEYWORD_MATCH: self._keyword_match_rerank,
            RerankingStrategy.RECENCY: self._recency_rerank,
            RerankingStrategy.RELEVANCE: self._relevance_rerank,
            RerankingStrategy.HYBRID: self._hybrid_rerank
        }
        
        logger.info("Reranker agent initialized")
    
    def rerank_documents(
        self,
        request: RerankingRequest,
        context: Optional[Dict[str, Any]] = None
    ) -> RerankingResult:
        """Rerank documents based on the request.
        
        Args:
            request: Reranking request with documents and parameters
            context: Optional context information
            
        Returns:
            RerankingResult with reranked documents
        """
        import time
        start_time = time.time()
        
        logger.info(f"Reranking {len(request.documents)} documents using {request.strategy.value} strategy")
        
        try:
            # Get the reranking function
            rerank_func = self.strategies.get(request.strategy, self.strategies[self.default_strategy])
            
            # Perform reranking
            reranked_docs = rerank_func(
                documents=request.documents,
                query=request.query,
                max_results=request.max_results,
                min_score=request.min_score,
                context=context or request.context
            )
            
            reranking_time = time.time() - start_time
            
            # Create result
            result = RerankingResult(
                documents=reranked_docs,
                original_count=len(request.documents),
                reranked_count=len(reranked_docs),
                reranking_time=reranking_time,
                strategy_used=request.strategy,
                metadata={
                    "max_results": request.max_results,
                    "min_score": request.min_score,
                    "context_provided": context is not None
                }
            )
            
            logger.info(f"Reranked {len(reranked_docs)} documents in {reranking_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error during document reranking: {e}")
            # Return original documents on error
            return RerankingResult(
                documents=request.documents[:request.max_results],
                original_count=len(request.documents),
                reranked_count=len(request.documents[:request.max_results]),
                reranking_time=time.time() - start_time,
                strategy_used=request.strategy,
                metadata={"error": str(e)}
            )
    
    def _score_only_rerank(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_results: int,
        min_score: float,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on similarity scores only.
        
        Args:
            documents: List of documents to rerank
            query: Original query
            max_results: Maximum number of results
            min_score: Minimum score threshold
            context: Optional context
            
        Returns:
            Reranked documents
        """
        # Sort by score (descending) and filter by minimum score
        filtered_docs = [doc for doc in documents if doc.get("score", 0) >= min_score]
        sorted_docs = sorted(filtered_docs, key=lambda x: x.get("score", 0), reverse=True)
        
        return sorted_docs[:max_results]
    
    def _keyword_match_rerank(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_results: int,
        min_score: float,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on keyword matching.
        
        Args:
            documents: List of documents to rerank
            query: Original query
            max_results: Maximum number of results
            min_score: Minimum score threshold
            context: Optional context
            
        Returns:
            Reranked documents
        """
        query_words = set(extract_terms(query))
        
        def calculate_keyword_score(doc):
            content = doc.get("content", "")
            overlap = keyword_overlap(query, content)
            total_query_words = len(query_words)
            
            if total_query_words == 0:
                return 0.0
            
            keyword_score = overlap / total_query_words
            
            # Combine with original score
            original_score = doc.get("score", 0)
            return (original_score * 0.7) + (keyword_score * 0.3)
        
        # Calculate new scores and sort
        for doc in documents:
            doc["keyword_score"] = calculate_keyword_score(doc)
        
        filtered_docs = [doc for doc in documents if doc.get("score", 0) >= min_score]
        sorted_docs = sorted(filtered_docs, key=lambda x: x["keyword_score"], reverse=True)
        
        return sorted_docs[:max_results]
    
    def _recency_rerank(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_results: int,
        min_score: float,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on recency.
        
        Args:
            documents: List of documents to rerank
            query: Original query
            max_results: Maximum number of results
            min_score: Minimum score threshold
            context: Optional context
            
        Returns:
            Reranked documents
        """
        from datetime import datetime
        
        def calculate_recency_score(doc):
            metadata = doc.get("metadata", {})
            created_at = metadata.get("created_at") or metadata.get("fetched_at")
            
            if not created_at:
                return 0.5  # Default score for documents without timestamps
            
            try:
                # Parse timestamp
                if isinstance(created_at, str):
                    doc_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    doc_time = created_at
                
                # Calculate recency score (newer = higher score)
                now = datetime.now()
                time_diff = (now - doc_time).total_seconds()
                
                # Normalize to 0-1 scale (documents from last 30 days get higher scores)
                recency_score = max(0, 1 - (time_diff / (30 * 24 * 3600)))
                
                # Combine with original score
                original_score = doc.get("score", 0)
                return (original_score * 0.8) + (recency_score * 0.2)
                
            except Exception:
                return doc.get("score", 0)
        
        # Calculate new scores and sort
        for doc in documents:
            doc["recency_score"] = calculate_recency_score(doc)
        
        filtered_docs = [doc for doc in documents if doc.get("score", 0) >= min_score]
        sorted_docs = sorted(filtered_docs, key=lambda x: x["recency_score"], reverse=True)
        
        return sorted_docs[:max_results]
    
    def _relevance_rerank(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_results: int,
        min_score: float,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on relevance heuristics.
        
        Args:
            documents: List of documents to rerank
            query: Original query
            max_results: Maximum number of results
            min_score: Minimum score threshold
            context: Optional context
            
        Returns:
            Reranked documents
        """
        def calculate_relevance_score(doc):
            content = doc.get("content", "").lower()
            query_lower = query.lower()
            
            # Check for exact phrase matches
            phrase_score = 1.0 if query_lower in content else 0.0
            
            # Check for word order preservation
            query_words = query_lower.split()
            content_words = content.split()
            
            order_score = 0.0
            if len(query_words) > 1:
                # Find positions of query words in content
                positions = []
                for word in query_words:
                    try:
                        pos = content_words.index(word)
                        positions.append(pos)
                    except ValueError:
                        positions.append(-1)
                
                # Calculate order preservation score
                if all(pos >= 0 for pos in positions):
                    # Check if positions are in ascending order
                    if positions == sorted(positions):
                        order_score = 1.0
                    else:
                        # Partial order preservation
                        order_score = 0.5
            
            # Check for title/heading relevance
            title_score = 0.0
            metadata = doc.get("metadata", {})
            title = metadata.get("title", "").lower()
            if title and any(word in title for word in query_words):
                title_score = 0.8
            
            # Combine scores
            original_score = doc.get("score", 0)
            relevance_score = (
                original_score * 0.5 +
                phrase_score * 0.3 +
                order_score * 0.1 +
                title_score * 0.1
            )
            
            return relevance_score
        
        # Calculate new scores and sort
        for doc in documents:
            doc["relevance_score"] = calculate_relevance_score(doc)
        
        filtered_docs = [doc for doc in documents if doc.get("score", 0) >= min_score]
        sorted_docs = sorted(filtered_docs, key=lambda x: x["relevance_score"], reverse=True)
        
        return sorted_docs[:max_results]
    
    def _hybrid_rerank(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_results: int,
        min_score: float,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents using a hybrid approach.
        
        Args:
            documents: List of documents to rerank
            query: Original query
            max_results: Maximum number of results
            min_score: Minimum score threshold
            context: Optional context
            
        Returns:
            Reranked documents
        """
        # Apply multiple strategies and combine results
        keyword_results = self._keyword_match_rerank(documents, query, max_results, min_score, context)
        relevance_results = self._relevance_rerank(documents, query, max_results, min_score, context)
        
        # Create a combined scoring system
        doc_scores = {}
        
        for doc in documents:
            doc_id = doc.get("id", "")
            
            # Get scores from different strategies
            keyword_score = next((d.get("keyword_score", 0) for d in keyword_results if d.get("id") == doc_id), 0)
            relevance_score = next((d.get("relevance_score", 0) for d in relevance_results if d.get("id") == doc_id), 0)
            original_score = doc.get("score", 0)
            
            # Combine scores with weights
            hybrid_score = (
                original_score * 0.4 +
                keyword_score * 0.3 +
                relevance_score * 0.3
            )
            
            doc_scores[doc_id] = hybrid_score
        
        # Sort by hybrid score
        for doc in documents:
            doc["hybrid_score"] = doc_scores.get(doc.get("id", ""), 0)
        
        filtered_docs = [doc for doc in documents if doc.get("score", 0) >= min_score]
        sorted_docs = sorted(filtered_docs, key=lambda x: x["hybrid_score"], reverse=True)
        
        return sorted_docs[:max_results]
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """Get reranking statistics.
        
        Returns:
            Dictionary with reranking statistics
        """
        return {
            "default_strategy": self.default_strategy.value,
            "available_strategies": [strategy.value for strategy in RerankingStrategy],
            "max_reranking_time": self.max_reranking_time
        }

# Convenience function for easy access
def create_reranker_agent(**kwargs) -> RerankerAgent:
    """Create a reranker agent with default settings.
    
    Args:
        **kwargs: Arguments to pass to RerankerAgent
        
    Returns:
        Configured RerankerAgent instance
    """
    return RerankerAgent(**kwargs)
