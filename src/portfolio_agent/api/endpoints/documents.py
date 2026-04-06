"""
Document ingestion endpoints backed by the canonical SDK path.
"""

import logging
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from ..models import DocumentRequest, DocumentResponse
from ...sdk import PortfolioAgent

logger = logging.getLogger(__name__)

router = APIRouter()


def get_agent(request: Request) -> PortfolioAgent:
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="PortfolioAgent is not initialized")
    return agent


@router.post("/documents", response_model=DocumentResponse)
async def add_document(request: DocumentRequest, agent: PortfolioAgent = Depends(get_agent)):
    """Index raw text into the local vector store."""

    try:
        result = agent.add_text(
            request.content,
            source=request.source or "api",
            metadata=request.metadata,
            document_type=request.document_type.value,
            redact_pii=request.redact_pii,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
        return DocumentResponse(
            document_id=result.document_id,
            chunks_created=result.chunks_created,
            processing_time=0.0,
            pii_detected=result.metadata.get("pii_redactions", 0),
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {e}") from e


@router.post("/documents/file", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), agent: PortfolioAgent = Depends(get_agent)):
    """Index an uploaded file via the supported file-ingestion SDK path."""

    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        result = agent.add_file(temp_path)
        return DocumentResponse(
            document_id=result.document_id,
            chunks_created=result.chunks_created,
            processing_time=0.0,
            pii_detected=result.metadata.get("pii_redactions", 0),
            metadata={**result.metadata, "filename": file.filename},
        )
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document upload failed: {e}") from e
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
