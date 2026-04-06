"""
API Middleware

This module provides custom middleware for the FastAPI application,
including request logging, security, rate limiting, and metrics collection.
"""

import time
import logging
import uuid
from typing import Callable, Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings
from ..security.pii_detector import AdvancedPIIDetector
from ..security.data_encryption import DataEncryption

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("request_logger")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            self.logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": process_time,
                    "timestamp": datetime.now().isoformat()
                },
                exc_info=True
            )
            raise

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security checks and validation."""
    
    def __init__(self, app):
        super().__init__(app)
        self.pii_detector = AdvancedPIIDetector()
        self.encryption = DataEncryption()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns in request
        if await self._is_suspicious_request(request):
            logger.warning(f"Suspicious request detected: {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "message": "Suspicious request detected"}
            )
        
        # Check for PII in request body (for POST/PUT requests)
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body and await self._contains_pii(body.decode('utf-8', errors='ignore')):
                logger.warning(f"PII detected in request body from {request.client.host}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Bad Request", "message": "PII detected in request"}
                )
        
        response = await call_next(request)
        return response
    
    async def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request appears suspicious."""
        # Check for SQL injection patterns
        suspicious_patterns = [
            "union select", "drop table", "delete from", "insert into",
            "script>", "javascript:", "onload=", "onerror="
        ]
        
        # Check URL path
        path = request.url.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path:
                return True
        
        # Check query parameters
        for param in request.query_params.values():
            param_lower = param.lower()
            for pattern in suspicious_patterns:
                if pattern in param_lower:
                    return True
        
        return False
    
    async def _contains_pii(self, text: str) -> bool:
        """Check if text contains PII."""
        try:
            result = self.pii_detector.detect_pii(text)
            return len(result.detected_pii) > 0
        except Exception as e:
            logger.error(f"Error checking for PII: {e}")
            return False

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(lambda: deque())
        self.limits = {
            "default": {"requests": 100, "window": 3600},  # 100 requests per hour
            "query": {"requests": 50, "window": 3600},     # 50 queries per hour
            "documents": {"requests": 20, "window": 3600}, # 20 document uploads per hour
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        endpoint_type = self._get_endpoint_type(request.url.path)
        
        if not self._is_rate_limited(client_ip, endpoint_type):
            response = await call_next(request)
            self._record_request(client_ip, endpoint_type)
            return response
        else:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests for {endpoint_type} endpoint",
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting."""
        if "/query" in path:
            return "query"
        elif "/documents" in path:
            return "documents"
        else:
            return "default"
    
    def _is_rate_limited(self, client_ip: str, endpoint_type: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        limit_config = self.limits.get(endpoint_type, self.limits["default"])
        window = limit_config["window"]
        max_requests = limit_config["requests"]
        
        # Clean old requests
        client_requests = self.requests[client_ip]
        while client_requests and client_requests[0] < now - window:
            client_requests.popleft()
        
        # Check if limit exceeded
        return len(client_requests) >= max_requests
    
    def _record_request(self, client_ip: str, endpoint_type: str) -> None:
        """Record a request for rate limiting."""
        now = time.time()
        self.requests[client_ip].append(now)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "response_times": deque(maxlen=1000),
            "endpoint_counts": defaultdict(int),
            "error_counts": defaultdict(int),
            "start_time": time.time()
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record successful request
            self._record_request(request, response, start_time, success=True)
            
            return response
            
        except Exception as e:
            # Record failed request
            self._record_request(request, None, start_time, success=False, error=str(e))
            raise
    
    def _record_request(self, request: Request, response: Response, start_time: float, 
                       success: bool, error: str = None) -> None:
        """Record request metrics."""
        process_time = time.time() - start_time
        
        # Update counters
        self.metrics["total_requests"] += 1
        if not success:
            self.metrics["total_errors"] += 1
            if error:
                self.metrics["error_counts"][error] += 1
        
        # Record response time
        self.metrics["response_times"].append(process_time)
        
        # Record endpoint count
        endpoint = f"{request.method} {request.url.path}"
        self.metrics["endpoint_counts"][endpoint] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        response_times = list(self.metrics["response_times"])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_requests": self.metrics["total_requests"],
            "total_errors": self.metrics["total_errors"],
            "average_response_time": avg_response_time,
            "uptime": time.time() - self.metrics["start_time"],
            "endpoint_counts": dict(self.metrics["endpoint_counts"]),
            "error_counts": dict(self.metrics["error_counts"]),
            "timestamp": datetime.now().isoformat()
        }

# Global metrics instance
metrics_middleware = MetricsMiddleware(None)

def get_metrics() -> Dict[str, Any]:
    """Get current metrics from the global metrics middleware."""
    return metrics_middleware.get_metrics()
