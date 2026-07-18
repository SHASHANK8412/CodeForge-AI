import threading
from backend.utils.cache import LRUCache, clear_cache, get_cache_stats, reset_cache_stats


def test_lru_cache_operations():
    cache = LRUCache(maxsize=3)

    # Cache starts empty
    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["current_size"] == 0

    # Cache miss
    assert cache.get("key1") is None
    assert cache.get_stats()["misses"] == 1

    # Cache set and hit
    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"
    assert cache.get_stats()["hits"] == 1

    # Cache eviction check (max size 3)
    cache.set("key2", "val2")
    cache.set("key3", "val3")
    assert cache.get_stats()["current_size"] == 3

    cache.set("key4", "val4")  # evicts key1 (least recently used)
    assert cache.get_stats()["current_size"] == 3
    assert cache.get("key1") is None
    assert cache.get("key2") == "val2"


def test_cache_global_functions():
    clear_cache()
    reset_cache_stats()

    stats = get_cache_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0


def test_cache_thread_safety():
    cache = LRUCache(maxsize=1000)

    def worker(worker_id: int):
        for i in range(100):
            cache.set(f"thread-{worker_id}-key-{i}", f"val-{i}")
            cache.get(f"thread-{worker_id}-key-{i}")

    threads = []
    for t in range(5):
        thread = threading.Thread(target=worker, args=(t,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    stats = cache.get_stats()
    assert stats["current_size"] == 500
    assert stats["hits"] == 500
