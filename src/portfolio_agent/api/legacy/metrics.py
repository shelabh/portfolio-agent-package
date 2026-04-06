"""
Metrics Endpoints

This module provides endpoints for system metrics and monitoring.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from ..models import MetricsResponse
from ..middleware import get_metrics
# Removed circular import - will use time.time() directly

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
async def get_system_metrics():
    """
    Get system metrics and performance statistics.
    
    This endpoint returns comprehensive metrics about the system performance.
    """
    try:
        # Get metrics from middleware
        middleware_metrics = get_metrics()
        
        # Calculate additional metrics
        uptime = middleware_metrics.get('uptime', 0)
        total_requests = middleware_metrics.get('total_requests', 0)
        total_errors = middleware_metrics.get('total_errors', 0)
        average_response_time = middleware_metrics.get('average_response_time', 0)
        
        # Get memory usage (simplified)
        import psutil
        memory_info = psutil.virtual_memory()
        
        return MetricsResponse(
            total_queries=total_requests,
            total_documents=0,  # TODO: Get from vector store
            average_response_time=average_response_time,
            active_sessions=0,  # TODO: Get from session manager
            memory_usage={
                "total": memory_info.total,
                "available": memory_info.available,
                "percent": memory_info.percent,
                "used": memory_info.used
            },
            performance_metrics={
                "uptime": uptime,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0,
                "requests_per_second": total_requests / uptime if uptime > 0 else 0
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        # Return basic metrics even if detailed ones fail
        return MetricsResponse(
            total_queries=0,
            total_documents=0,
            average_response_time=0.0,
            active_sessions=0,
            memory_usage={"total": 0, "available": 0, "percent": 0, "used": 0},
            performance_metrics={"uptime": 0, "total_requests": 0, "total_errors": 0, "error_rate": 0, "requests_per_second": 0}
        )

@router.get("/metrics/health")
async def get_health_metrics():
    """
    Get health-specific metrics.
    
    This endpoint returns metrics focused on system health and availability.
    """
    try:
        # Get basic system metrics
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_info.percent,
                "disk_percent": (disk_info.used / disk_info.total) * 100
            },
            "application": {
                "status": "healthy",
                "uptime": get_metrics().get('uptime', 0),
                "total_requests": get_metrics().get('total_requests', 0),
                "error_rate": get_metrics().get('total_errors', 0) / max(get_metrics().get('total_requests', 1), 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}", exc_info=True)
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }

@router.get("/metrics/performance")
async def get_performance_metrics():
    """
    Get performance-specific metrics.
    
    This endpoint returns metrics focused on application performance.
    """
    try:
        middleware_metrics = get_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "average_response_time": middleware_metrics.get('average_response_time', 0),
                "total_requests": middleware_metrics.get('total_requests', 0),
                "total_errors": middleware_metrics.get('total_errors', 0),
                "uptime": middleware_metrics.get('uptime', 0),
                "requests_per_second": middleware_metrics.get('total_requests', 0) / max(middleware_metrics.get('uptime', 1), 1)
            },
            "endpoints": middleware_metrics.get('endpoint_counts', {}),
            "errors": middleware_metrics.get('error_counts', {})
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }
