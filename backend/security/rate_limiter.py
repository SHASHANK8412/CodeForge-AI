"""
AIForge V2 — In-Memory API Rate Limiter
========================================
Protects expensive AI endpoints (/generate, /autopilot, /rag/search, /security/scan)
against excessive request flooding.
"""

import time
import logging
from typing import Dict, Tuple
from fastapi import HTTPException, status

_logger = logging.getLogger("aiforge.security.rate_limiter")


class RateLimiter:
    """
    In-memory window rate limiter configurable per endpoint.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = {}

    def check(self, key: str):
        now = time.time()
        timestamps = self._history.get(key, [])
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]

        if len(valid_timestamps) >= self.max_requests:
            _logger.warning(f"[RateLimiter] Rate limit exceeded for key '{key}'")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {self.max_requests} requests per {self.window_seconds}s allowed."
            )

        valid_timestamps.append(now)
        self._history[key] = valid_timestamps


global_rate_limiter = RateLimiter(max_requests=40, window_seconds=60)
