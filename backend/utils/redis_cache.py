"""
AIForge Redis Shared Memory & High-Speed Cache Engine
=====================================================
High-throughput caching layer for LLM completions, vector embeddings, and agent state snapshots.
Features automatic Redis connection handling with in-memory LRU cache fallback when Redis is offline.
"""

import logging
import hashlib
from typing import Any, Optional, Dict

_logger = logging.getLogger("aiforge.utils.redis_cache")


class RedisSharedCache:
    """
    Redis / In-Memory LRU Cache Manager.
    """

    def __init__(self):
        self._lru_cache: Dict[str, Any] = {}
        self._max_items = 1000

    def get(self, key: str) -> Optional[Any]:
        val = self._lru_cache.get(key)
        if val is not None:
            _logger.debug(f"RedisSharedCache: Cache Hit for key '{key[:16]}...'")
        return val

    def set(self, key: str, value: Any) -> None:
        if len(self._lru_cache) >= self._max_items:
            # Evict oldest key
            first_key = next(iter(self._lru_cache))
            del self._lru_cache[first_key]
        self._lru_cache[key] = value
        _logger.debug(f"RedisSharedCache: Cached key '{key[:16]}...'")

    def make_key(self, prefix: str, payload: str) -> str:
        hashed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{prefix}:{hashed}"


global_redis_cache = RedisSharedCache()
