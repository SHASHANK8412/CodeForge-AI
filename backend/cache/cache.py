"""
AIForge Day 28 — LLM Response & General Cache Manager
======================================================
Caches deterministic/reusable LLM operations with secret redaction and configurable TTLs.
Key includes: model, prompt_version, relevant configuration, and input_hash.
"""

import re
import json
import hashlib
import logging
from typing import Dict, Any, Optional

from backend.cache.redis import get_redis_client, is_redis_available, CACHE_ENABLED

_logger = logging.getLogger("aiforge.cache.llm")

DEFAULT_LLM_CACHE_TTL = 3600  # 1 hour
SECRET_REDACT_PATTERNS = [
    re.compile(r'(?i)(bearer\s+|jwt\s+|token=)[a-zA-Z0-9_\-\.]+\b'),
    re.compile(r'(?i)(password|passwd|secret|api_key|apikey)=[^&\s]+')
]


def sanitize_cache_content(content: str) -> str:
    if not isinstance(content, str):
        return content
    sanitized = content
    for pat in SECRET_REDACT_PATTERNS:
        sanitized = pat.sub("[REDACTED_SECRET]", sanitized)
    return sanitized


class LLMCacheManager:
    """
    Deterministic LLM response caching manager.
    """

    def __init__(self, default_ttl: int = DEFAULT_LLM_CACHE_TTL):
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def generate_cache_key(
        self,
        model: str,
        prompt_version: str,
        input_text: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        safe_input = sanitize_cache_content(input_text)
        config_str = json.dumps(config or {}, sort_keys=True)
        raw_key = f"llm:{model}:{prompt_version}:{config_str}:{safe_input}"
        h = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"aiforge:cache:{h}"

    def get(
        self,
        model: str,
        prompt_version: str,
        input_text: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not CACHE_ENABLED:
            return None

        client = get_redis_client()
        if client is None:
            return None

        key = self.generate_cache_key(model, prompt_version, input_text, config)
        try:
            val = client.get(key)
            if val:
                self.hits += 1
                _logger.info(f"[LLMCache] Cache HIT for key '{key[:16]}...'")
                return val.decode("utf-8") if isinstance(val, bytes) else str(val)
        except Exception as e:
            _logger.warning(f"[LLMCache] Redis get exception: {e}")

        self.misses += 1
        return None

    def set(
        self,
        model: str,
        prompt_version: str,
        input_text: str,
        response_text: str,
        config: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        if not CACHE_ENABLED:
            return False

        client = get_redis_client()
        if client is None:
            return False

        key = self.generate_cache_key(model, prompt_version, input_text, config)
        safe_response = sanitize_cache_content(response_text)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        try:
            client.set(key, safe_response, ex=ttl)
            _logger.info(f"[LLMCache] Cached response under key '{key[:16]}...' (TTL: {ttl}s)")
            return True

        except Exception as e:
            _logger.warning(f"[LLMCache] Redis set exception: {e}")
            return False

    def invalidate_project_cache(self, project_id: str) -> int:
        client = get_redis_client()
        if client is None:
            return 0
        try:
            keys = client.keys(f"aiforge:cache:*{project_id}*")
            if keys:
                return client.delete(*keys)
        except Exception:
            pass
        return 0


global_llm_cache_manager = LLMCacheManager()
