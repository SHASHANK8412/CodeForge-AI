from collections import OrderedDict
from threading import Lock
from typing import Any

from backend.config import MAX_CACHE_ITEMS


class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) cache with hit/miss statistics.
    """

    def __init__(self, maxsize: int = 128) -> None:
        self._maxsize = maxsize
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @maxsize.setter
    def maxsize(self, value: int) -> None:
        with self._lock:
            self._maxsize = value
            # Evict extra elements if maxsize decreased
            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def get(self, key: str) -> str | None:
        """
        Get cached value for key. Updates access order.
        """
        with self._lock:
            if key in self._cache:
                self._hits += 1
                self._cache.move_to_end(key)
                return self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: str) -> None:
        """
        Set key-value pair in cache. Evicts oldest entries if size exceeded.
        """
        with self._lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """
        Clear all entries and reset stats.
        """
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def reset_stats(self) -> None:
        """
        Reset cache hit and miss counters.
        """
        with self._lock:
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """
        Retrieve hit count, miss count, current cache size, and hit ratio.
        """
        with self._lock:
            total = self._hits + self._misses
            ratio = float(self._hits) / total if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": ratio,
                "current_size": len(self._cache),
                "max_size": self._maxsize,
            }


# Singleton cache instance using configuration size
llm_cache = LRUCache(maxsize=MAX_CACHE_ITEMS)


def get_cache_stats() -> dict[str, Any]:
    return llm_cache.get_stats()


def clear_cache() -> None:
    llm_cache.clear()


def reset_cache_stats() -> None:
    llm_cache.reset_stats()
