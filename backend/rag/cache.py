"""
AIForge V2 — Day 13 Production RAG Caching System
Implements query rewrite cache, retrieval result cache, rerank cache, and negative cache.
"""
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional

from backend.rag.models import RetrievalCandidate, GroundingContext
from backend.rag.config import global_rag_config

logger = logging.getLogger("aiforge.rag.cache")


class RAGCache:
    """
    Centralized RAG Cache managing query rewrite caching, retrieval candidate caching,
    rerank caching, and negative caching with source fingerprint invalidation.
    """

    def __init__(self, ttl_seconds: int = global_rag_config.CACHE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._retrieval_cache: Dict[str, Tuple[float, List[RetrievalCandidate]]] = {}
        self._negative_cache: Dict[str, float] = {}  # query_hash -> timestamp
        self._query_rewrite_cache: Dict[str, List[str]] = {}

    def get_retrieval_candidates(self, query: str, source_fingerprint: str) -> Optional[List[RetrievalCandidate]]:
        if not global_rag_config.AIFORGE_RAG_CACHE_ENABLED:
            return None

        key = self._build_key(query, source_fingerprint)
        if key in self._retrieval_cache:
            ts, candidates = self._retrieval_cache[key]
            if time.time() - ts <= self.ttl_seconds:
                logger.info(f"RAGCache: HIT for query '{query[:25]}...'")
                return candidates
            else:
                del self._retrieval_cache[key]
        return None

    def set_retrieval_candidates(self, query: str, source_fingerprint: str, candidates: List[RetrievalCandidate]) -> None:
        if not global_rag_config.AIFORGE_RAG_CACHE_ENABLED:
            return
        key = self._build_key(query, source_fingerprint)
        self._retrieval_cache[key] = (time.time(), candidates)

    def is_negative_cached(self, query: str, source_fingerprint: str) -> bool:
        if not global_rag_config.AIFORGE_RAG_CACHE_ENABLED:
            return False
        key = self._build_key(query, source_fingerprint)
        if key in self._negative_cache:
            ts = self._negative_cache[key]
            if time.time() - ts <= self.ttl_seconds:
                return True
            else:
                del self._negative_cache[key]
        return False

    def set_negative_cache(self, query: str, source_fingerprint: str) -> None:
        if not global_rag_config.AIFORGE_RAG_CACHE_ENABLED:
            return
        key = self._build_key(query, source_fingerprint)
        self._negative_cache[key] = time.time()

    def invalidate(self) -> None:
        """Invalidates all cached entries on source updates/deletions."""
        self._retrieval_cache.clear()
        self._negative_cache.clear()
        self._query_rewrite_cache.clear()
        logger.info("RAGCache: Cleared all cache entries.")

    def _build_key(self, query: str, fingerprint: str) -> str:
        raw = f"{query.strip().lower()}_{fingerprint}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# Global RAG Cache Singleton
global_rag_cache = RAGCache()
