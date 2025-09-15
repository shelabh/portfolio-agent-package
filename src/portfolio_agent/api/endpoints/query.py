"""
Query Endpoints

This module provides endpoints for querying the RAG pipeline.
"""

import time
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from ..models import (
    QueryRequest, QueryResponse, BatchQueryRequest, BatchQueryResponse,
    SearchRequest, SearchResponse, ErrorResponse
)
# Removed circular import - will create RAG pipeline locally
from ...rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_rag_pipeline() -> RAGPipeline:
    """Get RAG pipeline instance."""
    # Import the global RAG pipeline from server
    from ..server import rag_pipeline
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check server logs."
        )
    return rag_pipeline

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Process a single query through the RAG pipeline.
    
    This endpoint processes a query and returns a response with sources and metadata.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Create RAG request
        from ...rag_pipeline import RAGRequest
        rag_request = RAGRequest(
            query=request.query,
            session_id=request.session_id or "default_session",
            max_documents=request.max_results,
            include_sources=request.include_sources,
            context=request.metadata
        )
        
        # Process the query
        result = rag_pipeline.process_query(rag_request)
        
        processing_time = time.time() - start_time
        
        # Log query processing
        background_tasks.add_task(
            _log_query_processing,
            request.query,
            request.user_id,
            request.session_id,
            processing_time,
            len(result.sources)
        )
        
        return QueryResponse(
            response=result.response,
            query_type=request.query_type,
            sources=result.sources,
            confidence=0.8,  # Default confidence since RAGResponse doesn't have this
            processing_time=processing_time,
            tokens_used=None,  # RAGResponse doesn't track tokens
            session_id=result.session_id,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )

@router.post("/query/stream")
async def query_rag_stream(
    request: QueryRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Process a query with streaming response.
    
    This endpoint processes a query and streams the response as it's generated.
    """
    try:
        logger.info(f"Processing streaming query: {request.query[:100]}...")
        
        # Create a generator for streaming response
        async def generate_response():
            try:
                async for chunk in rag_pipeline.process_query_stream(
                    query=request.query,
                    query_type=request.query_type.value,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    max_results=request.max_results,
                    include_sources=request.include_sources,
                    persona=request.persona,
                    metadata=request.metadata
                ):
                    yield f"data: {chunk}\n\n"
                
                # Send end marker
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming query failed: {e}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming query setup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Streaming query setup failed: {str(e)}"
        )

@router.post("/query/batch", response_model=BatchQueryResponse)
async def query_batch(
    request: BatchQueryRequest,
    background_tasks: BackgroundTasks,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Process multiple queries in batch.
    
    This endpoint processes multiple queries and returns results for each.
    """
    start_time = time.time()
    batch_id = request.batch_id or f"batch_{int(time.time())}"
    
    try:
        logger.info(f"Processing batch query with {len(request.queries)} queries")
        
        results = []
        errors = []
        
        if request.parallel:
            # Process queries in parallel
            import asyncio
            
            async def process_single_query(query_req: QueryRequest) -> tuple:
                try:
                    result = await rag_pipeline.process_query(
                        query=query_req.query,
                        query_type=query_req.query_type.value,
                        user_id=query_req.user_id,
                        session_id=query_req.session_id,
                        max_results=query_req.max_results,
                        include_sources=query_req.include_sources,
                        persona=query_req.persona,
                        metadata=query_req.metadata
                    )
                    
                    return QueryResponse(
                        response=result.get('response', ''),
                        query_type=query_req.query_type,
                        sources=result.get('sources', []),
                        confidence=result.get('confidence', 0.0),
                        processing_time=result.get('processing_time', 0.0),
                        tokens_used=result.get('tokens_used'),
                        session_id=query_req.session_id,
                        metadata=result.get('metadata', {})
                    ), None
                    
                except Exception as e:
                    return None, ErrorResponse(
                        error="Query Processing Error",
                        message=str(e),
                        request_id=f"{batch_id}_{len(results)}"
                    )
            
            # Execute all queries in parallel
            tasks = [process_single_query(query_req) for query_req in request.queries]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result, error in batch_results:
                if result:
                    results.append(result)
                else:
                    errors.append(error)
        else:
            # Process queries sequentially
            for i, query_req in enumerate(request.queries):
                try:
                    result = await rag_pipeline.process_query(
                        query=query_req.query,
                        query_type=query_req.query_type.value,
                        user_id=query_req.user_id,
                        session_id=query_req.session_id,
                        max_results=query_req.max_results,
                        include_sources=query_req.include_sources,
                        persona=query_req.persona,
                        metadata=query_req.metadata
                    )
                    
                    results.append(QueryResponse(
                        response=result.get('response', ''),
                        query_type=query_req.query_type,
                        sources=result.get('sources', []),
                        confidence=result.get('confidence', 0.0),
                        processing_time=result.get('processing_time', 0.0),
                        tokens_used=result.get('tokens_used'),
                        session_id=query_req.session_id,
                        metadata=result.get('metadata', {})
                    ))
                    
                except Exception as e:
                    errors.append(ErrorResponse(
                        error="Query Processing Error",
                        message=str(e),
                        request_id=f"{batch_id}_{i}"
                    ))
        
        total_processing_time = time.time() - start_time
        
        # Log batch processing
        background_tasks.add_task(
            _log_batch_processing,
            batch_id,
            len(request.queries),
            len(results),
            len(errors),
            total_processing_time
        )
        
        return BatchQueryResponse(
            batch_id=batch_id,
            results=results,
            total_processing_time=total_processing_time,
            success_count=len(results),
            error_count=len(errors),
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Batch query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch query processing failed: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Search for documents in the vector store.
    
    This endpoint searches for documents based on similarity to the query.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Searching documents for: {request.query[:100]}...")
        
        # Perform search
        results = await rag_pipeline.search_documents(
            query=request.query,
            filters=request.filters,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )
        
        query_time = time.time() - start_time
        
        return SearchResponse(
            results=results.get('documents', []),
            total=results.get('total', 0),
            limit=request.limit,
            offset=request.offset,
            query_time=query_time,
            facets=results.get('facets')
        )
        
    except Exception as e:
        logger.error(f"Document search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Document search failed: {str(e)}"
        )

@router.get("/query/history")
async def get_query_history(
    user_id: str = None,
    session_id: str = None,
    limit: int = 50,
    offset: int = 0,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get query history for a user or session.
    
    This endpoint retrieves the history of queries for a specific user or session.
    """
    try:
        # Get query history from memory manager
        history = await rag_pipeline.get_query_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "history": history,
            "total": len(history),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get query history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get query history: {str(e)}"
        )

async def _log_query_processing(
    query: str,
    user_id: str,
    session_id: str,
    processing_time: float,
    source_count: int
) -> None:
    """Log query processing for analytics."""
    logger.info(
        f"Query processed: user={user_id}, session={session_id}, "
        f"time={processing_time:.2f}s, sources={source_count}"
    )

async def _log_batch_processing(
    batch_id: str,
    total_queries: int,
    success_count: int,
    error_count: int,
    total_time: float
) -> None:
    """Log batch processing for analytics."""
    logger.info(
        f"Batch processed: id={batch_id}, total={total_queries}, "
        f"success={success_count}, errors={error_count}, time={total_time:.2f}s"
    )
