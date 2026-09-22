"""
AIForge Day 28 — Redis Client & Resilience Manager
===================================================
Manages Redis connections with automatic fallback to fakeredis / in-memory dictionary
when a live Redis server is unreachable, ensuring safe offline operation.
"""

import os
import logging
from typing import Any, Optional

_logger = logging.getLogger("aiforge.cache.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

_redis_client = None
_is_real_redis = False


def _init_redis():
    global _redis_client, _is_real_redis
    if not CACHE_ENABLED:
        _logger.info("[RedisClient] Caching disabled via CACHE_ENABLED=false")
        return None

    try:
        import redis
        client = redis.from_url(REDIS_URL, socket_connect_timeout=1.0)
        client.ping()
        _redis_client = client
        _is_real_redis = True
        _logger.info(f"[RedisClient] Connected to live Redis at '{REDIS_URL}'")
        return _redis_client
    except Exception as e:
        _logger.info(f"[RedisClient] Live Redis connection notice ({e}); initializing fakeredis fallback.")

    try:
        import fakeredis
        _redis_client = fakeredis.FakeStrictRedis()
        _is_real_redis = False
        _logger.info("[RedisClient] Initialized fakeredis in-memory fallback client.")
        return _redis_client
    except Exception as ex:
        _logger.warning(f"[RedisClient] Fakeredis unavailable ({ex}); using basic pass-through.")
        return None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _init_redis()
    return _redis_client


def is_redis_available() -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:
        return False
