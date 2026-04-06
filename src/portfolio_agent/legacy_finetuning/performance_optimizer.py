"""
Performance Optimizer

This module provides performance optimization features including caching,
batching, async processing, and resource management.
"""

import logging
import time
import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from collections import defaultdict, deque
import queue

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = None
    ttl: Optional[timedelta] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl is None:
            return False
        return datetime.now() - self.created_at > self.ttl
    
    def access(self):
        """Record access to cache entry."""
        self.access_count += 1
        self.last_accessed = datetime.now()

class CacheManager:
    """Advanced cache manager with TTL and LRU eviction."""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[timedelta] = None,
        eviction_policy: str = "lru"
    ):
        """Initialize cache manager.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live for cache entries
            eviction_policy: Cache eviction policy ('lru', 'lfu', 'ttl')
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy
        
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = deque()  # For LRU
        self.access_counts = defaultdict(int)  # For LFU
        
        self._lock = threading.RLock()
        
        logger.info(f"Cache manager initialized with max_size={max_size}, policy={eviction_policy}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                if key in self.access_counts:
                    del self.access_counts[key]
                return None
            
            # Record access
            entry.access()
            self.access_counts[key] += 1
            
            # Update access order for LRU
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set value in cache."""
        with self._lock:
            # Use provided TTL or default
            entry_ttl = ttl or self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                ttl=entry_ttl
            )
            
            # Check if we need to evict
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            # Store entry
            self.cache[key] = entry
            self.access_order.append(key)
            self.access_counts[key] = 1
    
    def _evict(self) -> None:
        """Evict entries based on policy."""
        if not self.cache:
            return
        
        if self.eviction_policy == "lru":
            # Remove least recently used
            while self.access_order:
                key = self.access_order.popleft()
                if key in self.cache:
                    del self.cache[key]
                    del self.access_counts[key]
                    break
        
        elif self.eviction_policy == "lfu":
            # Remove least frequently used
            min_count = min(self.access_counts.values())
            for key, count in self.access_counts.items():
                if count == min_count:
                    del self.cache[key]
                    del self.access_counts[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
                    break
        
        elif self.eviction_policy == "ttl":
            # Remove expired entries
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self.cache[key]
                del self.access_counts[key]
                if key in self.access_order:
                    self.access_order.remove(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.access_counts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'max_size': self.max_size,
                'eviction_policy': self.eviction_policy,
                'default_ttl': str(self.default_ttl) if self.default_ttl else None
            }
    
    def cached(self, ttl: Optional[timedelta] = None):
        """Decorator for caching function results."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
                
                # Compute result
                logger.debug(f"Cache miss for {func.__name__}, computing...")
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

class BatchProcessor:
    """Batch processor for efficient batch operations."""
    
    def __init__(
        self,
        batch_size: int = 32,
        max_wait_time: float = 1.0,
        max_queue_size: int = 1000
    ):
        """Initialize batch processor.
        
        Args:
            batch_size: Maximum batch size
            max_wait_time: Maximum time to wait for batch completion
            max_queue_size: Maximum queue size
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.max_queue_size = max_queue_size
        
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.processing = False
        self.worker_thread = None
        
        logger.info(f"Batch processor initialized with batch_size={batch_size}")
    
    def start(self):
        """Start the batch processor."""
        if not self.processing:
            self.processing = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            logger.info("Batch processor started")
    
    def stop(self):
        """Stop the batch processor."""
        self.processing = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("Batch processor stopped")
    
    def add_request(
        self,
        request: Any,
        callback: Optional[Callable] = None
    ) -> None:
        """Add a request to the batch queue.
        
        Args:
            request: Request to process
            callback: Optional callback function
        """
        try:
            self.queue.put((request, callback), timeout=1.0)
        except queue.Full:
            logger.warning("Batch queue is full, dropping request")
    
    def _worker(self):
        """Worker thread for processing batches."""
        batch = []
        last_batch_time = time.time()
        
        while self.processing:
            try:
                # Try to get request with timeout
                try:
                    request, callback = self.queue.get(timeout=0.1)
                    batch.append((request, callback))
                except queue.Empty:
                    pass
                
                # Check if we should process batch
                current_time = time.time()
                should_process = (
                    len(batch) >= self.batch_size or
                    (batch and current_time - last_batch_time >= self.max_wait_time)
                )
                
                if should_process and batch:
                    self._process_batch(batch)
                    batch = []
                    last_batch_time = current_time
                
            except Exception as e:
                logger.error(f"Error in batch worker: {e}")
    
    def _process_batch(self, batch: List[tuple]):
        """Process a batch of requests."""
        logger.info(f"Processing batch of {len(batch)} requests")
        
        # Extract requests and callbacks
        requests = [item[0] for item in batch]
        callbacks = [item[1] for item in batch]
        
        # Process batch (this would be implemented by subclasses)
        results = self._execute_batch(requests)
        
        # Call callbacks
        for i, (result, callback) in enumerate(zip(results, callbacks)):
            if callback:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
    
    def _execute_batch(self, requests: List[Any]) -> List[Any]:
        """Execute batch processing. Override in subclasses."""
        # Default implementation - just return requests as-is
        return requests

class AsyncProcessor:
    """Async processor for concurrent operations."""
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize async processor.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.info(f"Async processor initialized with max_concurrent={max_concurrent}")
    
    async def process_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Process function asynchronously with concurrency control."""
        async with self.semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, func, *args, **kwargs)
    
    async def process_batch_async(
        self,
        func: Callable,
        items: List[Any],
        *args,
        **kwargs
    ) -> List[Any]:
        """Process a batch of items asynchronously."""
        tasks = [
            self.process_async(func, item, *args, **kwargs)
            for item in items
        ]
        return await asyncio.gather(*tasks)

class PerformanceOptimizer:
    """Main performance optimizer combining all optimization features."""
    
    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: Optional[timedelta] = None,
        batch_size: int = 32,
        max_concurrent: int = 10
    ):
        """Initialize performance optimizer.
        
        Args:
            cache_size: Cache size
            cache_ttl: Cache TTL
            batch_size: Batch size for processing
            max_concurrent: Maximum concurrent operations
        """
        self.cache_manager = CacheManager(
            max_size=cache_size,
            default_ttl=cache_ttl,
            eviction_policy="lru"
        )
        
        self.batch_processor = BatchProcessor(batch_size=batch_size)
        self.async_processor = AsyncProcessor(max_concurrent=max_concurrent)
        
        # Performance metrics
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_operations': 0,
            'async_operations': 0,
            'total_operations': 0
        }
        
        logger.info("Performance optimizer initialized")
    
    def start(self):
        """Start optimization services."""
        self.batch_processor.start()
        logger.info("Performance optimizer started")
    
    def stop(self):
        """Stop optimization services."""
        self.batch_processor.stop()
        logger.info("Performance optimizer stopped")
    
    def cached_function(
        self,
        ttl: Optional[timedelta] = None
    ):
        """Decorator for caching function results."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                self.metrics['total_operations'] += 1
                
                # Generate cache key
                key = self.cache_manager._generate_key(func.__name__, *args, **kwargs)
                
                # Try cache first
                cached_result = self.cache_manager.get(key)
                if cached_result is not None:
                    self.metrics['cache_hits'] += 1
                    return cached_result
                
                # Cache miss - compute result
                self.metrics['cache_misses'] += 1
                result = func(*args, **kwargs)
                
                # Store in cache
                self.cache_manager.set(key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    async def process_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Process function asynchronously."""
        self.metrics['async_operations'] += 1
        return await self.async_processor.process_async(func, *args, **kwargs)
    
    def add_to_batch(
        self,
        request: Any,
        callback: Optional[Callable] = None
    ):
        """Add request to batch processing."""
        self.metrics['batch_operations'] += 1
        self.batch_processor.add_request(request, callback)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        cache_stats = self.cache_manager.get_stats()
        
        total_ops = self.metrics['total_operations']
        cache_hit_rate = (
            self.metrics['cache_hits'] / total_ops
            if total_ops > 0 else 0
        )
        
        return {
            'cache_stats': cache_stats,
            'cache_hit_rate': cache_hit_rate,
            'metrics': self.metrics.copy(),
            'batch_processor_active': self.batch_processor.processing
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self.cache_manager.clear()
        logger.info("Cache cleared")
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_operations': 0,
            'async_operations': 0,
            'total_operations': 0
        }
        logger.info("Performance metrics reset")

# Convenience functions
def create_performance_optimizer(**kwargs) -> PerformanceOptimizer:
    """Create a performance optimizer instance."""
    return PerformanceOptimizer(**kwargs)

def create_cache_manager(**kwargs) -> CacheManager:
    """Create a cache manager instance."""
    return CacheManager(**kwargs)

def create_batch_processor(**kwargs) -> BatchProcessor:
    """Create a batch processor instance."""
    return BatchProcessor(**kwargs)

def create_async_processor(**kwargs) -> AsyncProcessor:
    """Create an async processor instance."""
    return AsyncProcessor(**kwargs)
