"""
AIForge Quality Recovery Day 14 — Centralized Cache Manager & Single-Flight Deduplication
==========================================================================================
Provides namespaced LRU caching with TTL, versioned cache key generation,
and single-flight request deduplication for concurrent expensive tasks.
"""

import time
import hashlib
import threading
import logging
from collections import OrderedDict
from typing import Dict, Any, Optional, Callable, Tuple

from backend.performance.config import global_performance_config

logger = logging.getLogger("aiforge.performance.cache_manager")


class LRUCache:
    """Thread-safe LRU Cache with TTL and size limits."""

    def __init__(self, maxsize: int = 1000, default_ttl: float = 3600.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                self.misses += 1
                return None
            val, expire_at = self._store[key]
            if time.time() > expire_at:
                del self._store[key]
                self.misses += 1
                return None
            self._store.move_to_end(key)
            self.hits += 1
            return val

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            expire_at = time.time() + (ttl if ttl is not None else self.default_ttl)
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, expire_at)
            if len(self._store) > self.maxsize:
                self._store.popitem(last=False)
                self.evictions += 1

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round(self.hits / total, 4) if total > 0 else 0.0


class SingleFlight:
    """
    Prevents duplicate concurrent work for identical expensive operations.
    Concurrent callers awaiting the same key will block until the single in-flight task finishes.
    """

    def __init__(self):
        self._in_flight: Dict[str, threading.Event] = {}
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, Exception] = {}
        self._lock = threading.Lock()

    def execute(self, key: str, func: Callable[[], Any]) -> Any:
        with self._lock:
            if key in self._in_flight:
                event = self._in_flight[key]
                wait = True
            else:
                event = threading.Event()
                self._in_flight[key] = event
                wait = False

        if wait:
            event.wait()
            if key in self._errors:
                raise self._errors[key]
            return self._results[key]

        try:
            res = func()
            with self._lock:
                self._results[key] = res
            return res
        except Exception as ex:
            with self._lock:
                self._errors[key] = ex
            raise ex
        finally:
            with self._lock:
                event.set()
                # Clean up singleflight state after notification
                self._in_flight.pop(key, None)
                # Schedules result cleanup
                threading.Thread(target=self._cleanup, args=(key,), daemon=True).start()

    def _cleanup(self, key: str) -> None:
        time.sleep(0.5)
        with self._lock:
            self._results.pop(key, None)
            self._errors.pop(key, None)


class CacheManager:
    """
    Centralized manager maintaining namespaced LRU caches:
    'classification', 'embedding', 'retrieval', 'repository', 'llm', 'evaluation'.
    """

    def __init__(self):
        self._namespaces: Dict[str, LRUCache] = {
            "classification": LRUCache(maxsize=500, default_ttl=7200.0),
            "embedding": LRUCache(maxsize=2000, default_ttl=86400.0),
            "retrieval": LRUCache(maxsize=500, default_ttl=3600.0),
            "repository": LRUCache(maxsize=200, default_ttl=1800.0),
            "llm": LRUCache(maxsize=500, default_ttl=3600.0),
            "evaluation": LRUCache(maxsize=100, default_ttl=3600.0),
        }
        self.single_flight = SingleFlight()

    def get_namespace(self, name: str) -> LRUCache:
        if name not in self._namespaces:
            self._namespaces[name] = LRUCache(maxsize=500, default_ttl=3600.0)
        return self._namespaces[name]

    def build_key(
        self,
        prompt_or_text: str,
        namespace: str = "general",
        model: Optional[str] = None,
        source_fingerprint: Optional[str] = None
    ) -> str:
        """Constructs a versioned, collision-resistant cache key."""
        p_version = global_performance_config.PROMPT_VERSION
        m_version = model or global_performance_config.MODEL_VERSION
        fp = source_fingerprint or "no_fp"
        text_hash = hashlib.sha256(prompt_or_text.encode("utf-8")).hexdigest()[:16]
        return f"{namespace}:{p_version}:{m_version}:{fp}:{text_hash}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        return self.get_namespace(namespace).get(key)

    def put(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None) -> None:
        self.get_namespace(namespace).put(key, value, ttl)

    def clear_all(self) -> None:
        for ns in self._namespaces.values():
            ns.clear()

    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        for ns_name, cache in self._namespaces.items():
            stats[ns_name] = {
                "hits": cache.hits,
                "misses": cache.misses,
                "evictions": cache.evictions,
                "hit_rate": cache.hit_rate
            }
        return stats


global_cache_manager = CacheManager()
