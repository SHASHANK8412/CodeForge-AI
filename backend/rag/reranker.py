"""
AIForge V2 — Day 13 Reranker & Context Prioritizer
Reranks retrieval candidates using structural features, exact symbol/path matches,
user-specified document priority, and minimum relevance threshold filtering.
"""
import re
import logging
from typing import Dict, Any, List, Optional

from backend.rag.models import RetrievalCandidate, RetrievalDecision
from backend.rag.config import global_rag_config

logger = logging.getLogger("aiforge.rag.reranker")


class Reranker:
    """
    Reranker scores and orders candidate chunks.
    Boosts: exact symbol match, explicit filename match, heading match, document priority.
    Filters: candidates below global_rag_config.MIN_RETRIEVAL_RELEVANCE threshold.
    """

    def rerank(
        self,
        candidates: List[RetrievalCandidate],
        query: str,
        decision: Optional[RetrievalDecision] = None,
        top_k: int = 10
    ) -> List[RetrievalCandidate]:
        if not global_rag_config.AIFORGE_RERANK_ENABLED or not candidates:
            return candidates[:top_k]

        q_lower = query.lower()
        reranked: List[RetrievalCandidate] = []

        for cand in candidates:
            boosted_score = cand.score

            # 1. Boost for explicit document priority in prompt (e.g. "According to architecture.pdf...")
            source_name = cand.metadata.get("source", "").lower() or cand.metadata.get("path", "").lower()
            if source_name and source_name in q_lower:
                boosted_score += 0.30

            # 2. Boost for exact symbol match
            symbol = cand.metadata.get("symbol", "").lower()
            if symbol and symbol in q_lower:
                boosted_score += 0.25

            # 3. Boost for explicit filename match
            path = cand.metadata.get("path", "").lower()
            if path and any(p in q_lower for p in path.split("/")):
                boosted_score += 0.20

            # 4. Boost for heading / section match
            heading = cand.metadata.get("heading", "").lower()
            if heading and heading in q_lower:
                boosted_score += 0.15

            # 6. Penalize candidates with zero token overlap for key query nouns
            stop_words = {"what", "where", "which", "does", "this", "according", "used", "with", "from", "handled", "defined", "summarize", "uploaded", "document", "explain", "index", "contain", "raw", "api", "key", "keys", "comment", "comments", "codebase", "implementation", "repo", "repository"}
            q_nouns = {w for w in re.findall(r"\b[a-zA-Z]{4,}\b", q_lower) if w not in stop_words}
            c_text_lower = cand.text.lower()
            if q_nouns and not any(w in c_text_lower for w in q_nouns) and len(candidates) > 1:
                boosted_score *= 0.15

            # Construct copy with reranked score
            reranked_cand = RetrievalCandidate(
                chunk_id=cand.chunk_id,
                source_id=cand.source_id,
                domain=cand.domain,
                score=round(boosted_score, 4),
                retrieval_method=cand.retrieval_method,
                text=cand.text,
                metadata=cand.metadata
            )
            reranked.append(reranked_cand)

        # Sort by reranked score descending
        reranked.sort(key=lambda x: x.score, reverse=True)

        # Filter by minimum relevance threshold
        threshold = global_rag_config.MIN_RETRIEVAL_RELEVANCE
        filtered = [c for c in reranked if c.score >= threshold]

        logger.info(f"Reranker: Input {len(candidates)} candidates -> Reranked & filtered ({len(filtered)} >= {threshold})")
        return filtered[:top_k]


# Global Reranker Singleton
global_reranker = Reranker()
