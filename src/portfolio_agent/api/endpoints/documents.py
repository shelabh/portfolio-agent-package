"""
Document Endpoints

This module provides endpoints for document management and processing.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models import DocumentRequest, DocumentResponse, SearchRequest, SearchResponse
# Removed circular import - will create RAG pipeline locally
from ...rag_pipeline import RAGPipeline
from ...ingestion import (
    GitHubIngestor, ResumeIngestor, WebsiteIngestor, GenericIngestor
)

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

@router.post("/documents", response_model=DocumentResponse)
async def add_document(
    request: DocumentRequest,
    background_tasks: BackgroundTasks,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Add a document to the vector store.
    
    This endpoint processes and indexes a document for retrieval.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Adding document: type={request.document_type}, source={request.source}")
        
        # Process the document using vector store and embedder directly
        from ...embeddings.openai_embedder import OpenAIEmbedder
        from ...vector_stores.faiss_store import FAISSVectorStore
        from ...ingestion.chunker import text_chunker
        from ...ingestion.pii_redactor import pii_redactor
        import uuid
        
        # Create components for document processing
        embedder = OpenAIEmbedder()
        vector_store = FAISSVectorStore()
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Redact PII if requested
        content = request.content
        pii_detected = 0
        if request.redact_pii:
            content, pii_stats = pii_redactor.redact_pii(content)
            pii_detected = sum(pii_stats.values())
        
        # Create text chunker with requested parameters
        chunker = text_chunker.__class__(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        # Chunk the document
        chunk_metadata = {"source": request.source, "document_type": request.document_type.value}
        chunk_objects = chunker.chunk_text(content, chunk_metadata)
        chunks = [chunk["content"] for chunk in chunk_objects]
        
        # Create document metadata
        doc_metadata = {
            "document_id": document_id,
            "source": request.source,
            "document_type": request.document_type.value,
            "chunk_count": len(chunks),
            "pii_detected": pii_detected,
            **(request.metadata or {})
        }
        
        # Add chunks to vector store
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_metadata = {
                **doc_metadata,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "chunk_size": len(chunk)
            }
            
            # Generate embedding and add to vector store
            embedding = await embedder.embed_single(chunk)
            vector_store.add_document(
                document_id=chunk_id,
                content=chunk,
                embedding=embedding,
                metadata=chunk_metadata
            )
        
        result = {
            "document_id": document_id,
            "chunks_created": len(chunks),
            "pii_detected": pii_detected,
            "metadata": doc_metadata
        }
        
        processing_time = time.time() - start_time
        
        # Log document processing
        background_tasks.add_task(
            _log_document_processing,
            result.get('document_id'),
            request.document_type.value,
            result.get('chunks_created', 0),
            processing_time
        )
        
        return DocumentResponse(
            document_id=result.get('document_id', ''),
            chunks_created=result.get('chunks_created', 0),
            processing_time=processing_time,
            pii_detected=result.get('pii_detected', 0),
            metadata=result.get('metadata', {})
        )
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}"
        )

@router.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    redact_pii: bool = Form(True),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Upload and process a document file.
    
    This endpoint accepts file uploads and processes them for indexing.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Uploading document: {file.filename}, type={file.content_type}")
        
        # Read file content
        content = await file.read()
        
        # Determine document type from file extension
        document_type = _get_document_type_from_filename(file.filename)
        
        # Process the document
        result = await rag_pipeline.add_document(
            content=content.decode('utf-8', errors='ignore'),
            document_type=document_type,
            source=source or file.filename,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content)
            },
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            redact_pii=redact_pii
        )
        
        processing_time = time.time() - start_time
        
        # Log document processing
        background_tasks.add_task(
            _log_document_processing,
            result.get('document_id'),
            document_type,
            result.get('chunks_created', 0),
            processing_time
        )
        
        return DocumentResponse(
            document_id=result.get('document_id', ''),
            chunks_created=result.get('chunks_created', 0),
            processing_time=processing_time,
            pii_detected=result.get('pii_detected', 0),
            metadata=result.get('metadata', {})
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {str(e)}"
        )

@router.post("/documents/github")
async def ingest_github_repository(
    background_tasks: BackgroundTasks,
    repository_url: str = Form(...),
    branch: str = Form("main"),
    include_patterns: Optional[str] = Form(None),
    exclude_patterns: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    redact_pii: bool = Form(True),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Ingest a GitHub repository.
    
    This endpoint fetches and processes files from a GitHub repository.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Ingesting GitHub repository: {repository_url}")
        
        # Create GitHub ingestor
        ingestor = GitHubIngestor()
        
        # Parse include/exclude patterns
        include_list = include_patterns.split(',') if include_patterns else None
        exclude_list = exclude_patterns.split(',') if exclude_patterns else None
        
        # Ingest repository
        documents = await ingestor.ingest_repository(
            repository_url=repository_url,
            branch=branch,
            include_patterns=include_list,
            exclude_patterns=exclude_list,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            redact_pii=redact_pii
        )
        
        # Add documents to vector store
        results = []
        for doc in documents:
            result = await rag_pipeline.add_document(
                content=doc['content'],
                document_type='md',  # GitHub files are typically markdown/code
                source=doc['source'],
                metadata=doc['metadata'],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                redact_pii=redact_pii
            )
            results.append(result)
        
        processing_time = time.time() - start_time
        total_chunks = sum(r.get('chunks_created', 0) for r in results)
        total_pii = sum(r.get('pii_detected', 0) for r in results)
        
        # Log repository ingestion
        background_tasks.add_task(
            _log_repository_ingestion,
            repository_url,
            len(documents),
            total_chunks,
            processing_time
        )
        
        return {
            "repository_url": repository_url,
            "documents_processed": len(documents),
            "chunks_created": total_chunks,
            "pii_detected": total_pii,
            "processing_time": processing_time,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"GitHub repository ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"GitHub repository ingestion failed: {str(e)}"
        )

@router.post("/documents/website")
async def ingest_website(
    background_tasks: BackgroundTasks,
    website_url: str = Form(...),
    max_pages: int = Form(10),
    max_depth: int = Form(2),
    delay: float = Form(1.0),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    redact_pii: bool = Form(True),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Ingest a website.
    
    This endpoint crawls and processes pages from a website.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Ingesting website: {website_url}")
        
        # Create website ingestor
        ingestor = WebsiteIngestor()
        
        # Ingest website
        documents = await ingestor.ingest_website(
            website_url=website_url,
            max_pages=max_pages,
            max_depth=max_depth,
            delay=delay,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            redact_pii=redact_pii
        )
        
        # Add documents to vector store
        results = []
        for doc in documents:
            result = await rag_pipeline.add_document(
                content=doc['content'],
                document_type='html',
                source=doc['source'],
                metadata=doc['metadata'],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                redact_pii=redact_pii
            )
            results.append(result)
        
        processing_time = time.time() - start_time
        total_chunks = sum(r.get('chunks_created', 0) for r in results)
        total_pii = sum(r.get('pii_detected', 0) for r in results)
        
        # Log website ingestion
        background_tasks.add_task(
            _log_website_ingestion,
            website_url,
            len(documents),
            total_chunks,
            processing_time
        )
        
        return {
            "website_url": website_url,
            "pages_processed": len(documents),
            "chunks_created": total_chunks,
            "pii_detected": total_pii,
            "processing_time": processing_time,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Website ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Website ingestion failed: {str(e)}"
        )

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get a specific document by ID.
    
    This endpoint retrieves document information and metadata.
    """
    try:
        document = await rag_pipeline.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Delete a document by ID.
    
    This endpoint removes a document and all its chunks from the vector store.
    """
    try:
        success = await rag_pipeline.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Log document deletion
        background_tasks.add_task(
            _log_document_deletion,
            document_id
        )
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/documents")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    source: Optional[str] = None,
    document_type: Optional[str] = None,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    List documents in the vector store.
    
    This endpoint retrieves a paginated list of documents with optional filtering.
    """
    try:
        documents = await rag_pipeline.list_documents(
            limit=limit,
            offset=offset,
            source=source,
            document_type=document_type
        )
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )

def _get_document_type_from_filename(filename: str) -> str:
    """Determine document type from filename extension."""
    if not filename:
        return 'txt'
    
    extension = filename.lower().split('.')[-1]
    
    type_mapping = {
        'pdf': 'pdf',
        'txt': 'txt',
        'md': 'md',
        'html': 'html',
        'htm': 'html',
        'json': 'json',
        'docx': 'docx',
        'doc': 'docx'
    }
    
    return type_mapping.get(extension, 'txt')

async def _log_document_processing(
    document_id: str,
    document_type: str,
    chunks_created: int,
    processing_time: float
) -> None:
    """Log document processing for analytics."""
    logger.info(
        f"Document processed: id={document_id}, type={document_type}, "
        f"chunks={chunks_created}, time={processing_time:.2f}s"
    )

async def _log_repository_ingestion(
    repository_url: str,
    documents_count: int,
    chunks_created: int,
    processing_time: float
) -> None:
    """Log repository ingestion for analytics."""
    logger.info(
        f"Repository ingested: url={repository_url}, documents={documents_count}, "
        f"chunks={chunks_created}, time={processing_time:.2f}s"
    )

async def _log_website_ingestion(
    website_url: str,
    pages_count: int,
    chunks_created: int,
    processing_time: float
) -> None:
    """Log website ingestion for analytics."""
    logger.info(
        f"Website ingested: url={website_url}, pages={pages_count}, "
        f"chunks={chunks_created}, time={processing_time:.2f}s"
    )

async def _log_document_deletion(document_id: str) -> None:
    """Log document deletion for analytics."""
    logger.info(f"Document deleted: id={document_id}")
