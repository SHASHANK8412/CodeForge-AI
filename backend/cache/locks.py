"""
AIForge Day 28 — Distributed Lock Manager
========================================
Prevents concurrent duplicate expensive workflows (e.g. parallel project generation)
using Redis locks with enforced TTL expiration (no infinite locks).
"""

import time
import secrets
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from backend.cache.redis import get_redis_client

_logger = logging.getLogger("aiforge.cache.locks")

DEFAULT_LOCK_TTL_SECONDS = 60  # Maximum 60 seconds TTL


class DistributedLockManager:
    """
    Redis-backed distributed lock manager.
    """

    def acquire_lock(self, lock_name: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS) -> Optional[str]:
        client = get_redis_client()
        if client is None:
            # Fallback: return dummy token if Redis offline
            return f"fallback_token_{secrets.token_hex(4)}"

        # Enforce positive TTL (max 300 seconds)
        ttl = max(1, min(ttl_seconds, 300))
        token = f"token_{secrets.token_urlsafe(8)}"
        key = f"aiforge:lock:{lock_name}"

        try:
            # NX = Only set if not exists, EX = Expiration in seconds
            acquired = client.set(key, token, nx=True, ex=ttl)
            if acquired:
                _logger.info(f"[LockManager] Acquired lock '{lock_name}' (TTL: {ttl}s)")
                return token
            else:
                _logger.warning(f"[LockManager] Lock '{lock_name}' is already held by another process.")
                return None
        except Exception as e:
            _logger.warning(f"[LockManager] Redis acquire lock notice: {e}")
            return token

    def release_lock(self, lock_name: str, token: str) -> bool:
        client = get_redis_client()
        if client is None or not token:
            return True

        key = f"aiforge:lock:{lock_name}"
        try:
            val = client.get(key)
            val_str = val.decode("utf-8") if isinstance(val, bytes) else str(val) if val else None
            if val_str == token:
                client.delete(key)
                _logger.info(f"[LockManager] Released lock '{lock_name}'")
                return True
        except Exception as e:
            _logger.warning(f"[LockManager] Redis release lock notice: {e}")

        return False

    @contextmanager
    def lock(self, lock_name: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS) -> Generator[bool, None, None]:
        token = self.acquire_lock(lock_name, ttl_seconds)
        acquired = token is not None
        try:
            yield acquired
        finally:
            if acquired and token:
                self.release_lock(lock_name, token)


global_distributed_lock_manager = DistributedLockManager()
