"""
AIForge Day 28 — API Rate Limiter
=================================
Sliding window rate limiter using Redis for FastAPI endpoints.
"""

import time
import logging
from typing import Dict, Any, Tuple, Optional

from backend.cache.redis import get_redis_client

_logger = logging.getLogger("aiforge.cache.ratelimit")

DEFAULT_LIMIT = 30  # 30 requests per minute by default


class RateLimiter:
    """
    Redis-backed sliding window rate limiter.
    """

    def is_rate_limited(
        self,
        identifier: str,
        endpoint: str = "default",
        max_requests: int = DEFAULT_LIMIT,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Returns (is_limited, remaining_requests, retry_after_seconds).
        """
        client = get_redis_client()
        if client is None:
            # Fallback: allow request if Redis unavailable
            return False, max_requests, 0

        now = int(time.time())
        key = f"aiforge:ratelimit:{endpoint}:{identifier}"
        window_start = now - window_seconds

        try:
            # Clean old entries
            client.zremrangebyscore(key, 0, window_start)
            # Count requests in window
            current_count = client.zcard(key)

            if current_count >= max_requests:
                oldest = client.zrange(key, 0, 0, withscores=True)
                retry_after = 1
                if oldest:
                    retry_after = max(1, int(oldest[0][1] + window_seconds - now))

                _logger.warning(f"[RateLimiter] Limit exceeded for '{identifier}' on '{endpoint}'")
                return True, 0, retry_after

            # Add current request
            client.zadd(key, {f"{now}_{time.time_ns()}": now})
            client.expire(key, window_seconds + 5)
            remaining = max(0, max_requests - (current_count + 1))
            return False, remaining, 0

        except Exception as e:
            _logger.warning(f"[RateLimiter] Redis rate limit notice: {e}")
            return False, max_requests, 0


global_rate_limiter = RateLimiter()
