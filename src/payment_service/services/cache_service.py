"""In-memory cache service with thread-safe operations."""

import asyncio
import time
import threading
from typing import Any, Dict, Optional
import structlog

from payment_service.config import settings


class CacheService:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.max_size = settings.cache_max_size
        self.default_ttl = settings.cache_ttl
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start background task to clean up expired entries."""
        async def cleanup_expired():
            while True:
                try:
                    await asyncio.sleep(60)  # Run cleanup every minute
                    await self._cleanup_expired_entries()
                except Exception as e:
                    self.logger.error("Cache cleanup error", error=str(e))
        
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(cleanup_expired())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Check if expired
            if current_time > entry['expires_at']:
                del self._cache[key]
                return None
            
            # Update access time
            entry['accessed_at'] = current_time
            
            self.logger.debug("Cache hit", key=key)
            return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        current_time = time.time()
        
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            self._cache[key] = {
                'value': value,
                'expires_at': current_time + ttl,
                'created_at': current_time,
                'accessed_at': current_time,
            }
            
            self.logger.debug("Cache set", key=key, ttl=ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.logger.debug("Cache delete", key=key)
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self.logger.info("Cache cleared")
    
    async def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            current_time = time.time()
            expired_count = 0
            
            for entry in self._cache.values():
                if current_time > entry['expires_at']:
                    expired_count += 1
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'expired_entries': expired_count,
                'default_ttl': self.default_ttl,
            }
    
    async def _cleanup_expired_entries(self) -> None:
        """Remove expired entries from cache."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time > entry['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self.logger.debug("Cleaned up expired cache entries", count=len(expired_keys))
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        with self._lock:
            if not self._cache:
                return
            
            # Find LRU entry
            lru_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k]['accessed_at']
            )
            
            del self._cache[lru_key]
            self.logger.debug("Evicted LRU cache entry", key=lru_key)
    
    def shutdown(self) -> None:
        """Shutdown cache service."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        with self._lock:
            self._cache.clear()
        
        self.logger.info("Cache service shutdown")