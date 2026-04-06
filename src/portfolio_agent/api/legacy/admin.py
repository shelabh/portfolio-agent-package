"""
Admin Endpoints

This module provides administrative endpoints for system management.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Header

from ..models import AdminRequest, AdminResponse
# Removed circular import - will create RAG pipeline locally
from ...rag_pipeline import RAGPipeline
from ...config import settings

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

# Simple admin key validation (in production, use proper authentication)
ADMIN_KEY = "admin_key_123"  # This should be in environment variables

async def verify_admin_key(x_admin_key: str = Header(None)):
    """Verify admin authentication key."""
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key

@router.post("/admin/actions", response_model=AdminResponse)
async def execute_admin_action(
    request: AdminRequest,
    admin_key: str = Depends(verify_admin_key),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Execute administrative actions.
    
    This endpoint allows administrators to perform system management tasks.
    """
    try:
        logger.info(f"Executing admin action: {request.action}")
        
        if request.admin_key != ADMIN_KEY:
            raise HTTPException(status_code=401, detail="Invalid admin key")
        
        # Execute the requested action
        result = await _execute_action(request.action, request.parameters, rag_pipeline)
        
        return AdminResponse(
            success=True,
            message=f"Action '{request.action}' executed successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin action failed: {e}", exc_info=True)
        return AdminResponse(
            success=False,
            message=f"Action '{request.action}' failed: {str(e)}",
            data=None
        )

@router.get("/admin/status")
async def get_admin_status(
    admin_key: str = Depends(verify_admin_key),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get system status for administrators.
    
    This endpoint provides detailed system status information.
    """
    try:
        # Get system status
        status = await rag_pipeline.get_system_status()
        
        return {
            "status": "operational",
            "components": status.get('components', {}),
            "metrics": status.get('metrics', {}),
            "configuration": {
                "local_only": settings.LOCAL_ONLY,
                "redact_pii": settings.REDACT_PII,
                "auto_email": settings.AUTO_EMAIL,
                "consent_required": settings.CONSENT_REQUIRED
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get admin status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get admin status: {str(e)}"
        )

@router.post("/admin/backup")
async def create_backup(
    admin_key: str = Depends(verify_admin_key),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Create a system backup.
    
    This endpoint creates a backup of the system data and configuration.
    """
    try:
        logger.info("Creating system backup")
        
        # Create backup
        backup_info = await rag_pipeline.create_backup()
        
        return {
            "message": "Backup created successfully",
            "backup_id": backup_info.get('backup_id'),
            "backup_path": backup_info.get('backup_path'),
            "backup_size": backup_info.get('backup_size'),
            "created_at": backup_info.get('created_at')
        }
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Backup creation failed: {str(e)}"
        )

@router.post("/admin/restore")
async def restore_backup(
    backup_id: str,
    admin_key: str = Depends(verify_admin_key),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Restore from a backup.
    
    This endpoint restores the system from a specified backup.
    """
    try:
        logger.info(f"Restoring from backup: {backup_id}")
        
        # Restore from backup
        restore_info = await rag_pipeline.restore_backup(backup_id)
        
        return {
            "message": "Backup restored successfully",
            "backup_id": backup_id,
            "restored_at": restore_info.get('restored_at'),
            "restored_components": restore_info.get('restored_components', [])
        }
        
    except Exception as e:
        logger.error(f"Backup restore failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Backup restore failed: {str(e)}"
        )

@router.post("/admin/clear-cache")
async def clear_cache(
    admin_key: str = Depends(verify_admin_key),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Clear system caches.
    
    This endpoint clears all system caches to free up memory.
    """
    try:
        logger.info("Clearing system caches")
        
        # Clear caches
        cleared = await rag_pipeline.clear_caches()
        
        return {
            "message": "Caches cleared successfully",
            "cleared_caches": cleared.get('cleared_caches', []),
            "freed_memory": cleared.get('freed_memory', 0)
        }
        
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cache clearing failed: {str(e)}"
        )

@router.post("/admin/reindex")
async def reindex_documents(
    admin_key: str = Depends(verify_admin_key),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Reindex all documents.
    
    This endpoint rebuilds the vector index for all documents.
    """
    try:
        logger.info("Reindexing all documents")
        
        # Reindex documents
        reindex_info = await rag_pipeline.reindex_documents()
        
        return {
            "message": "Documents reindexed successfully",
            "documents_processed": reindex_info.get('documents_processed', 0),
            "processing_time": reindex_info.get('processing_time', 0),
            "index_size": reindex_info.get('index_size', 0)
        }
        
    except Exception as e:
        logger.error(f"Document reindexing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Document reindexing failed: {str(e)}"
        )

async def _execute_action(action: str, parameters: Dict[str, Any], rag_pipeline: RAGPipeline) -> Dict[str, Any]:
    """Execute the specified admin action."""
    
    if action == "status":
        return await rag_pipeline.get_system_status()
    
    elif action == "backup":
        return await rag_pipeline.create_backup()
    
    elif action == "restore":
        backup_id = parameters.get('backup_id')
        if not backup_id:
            raise ValueError("backup_id parameter is required")
        return await rag_pipeline.restore_backup(backup_id)
    
    elif action == "clear_cache":
        return await rag_pipeline.clear_caches()
    
    elif action == "reindex":
        return await rag_pipeline.reindex_documents()
    
    elif action == "reset":
        return await rag_pipeline.reset_system()
    
    else:
        raise ValueError(f"Unknown action: {action}")
