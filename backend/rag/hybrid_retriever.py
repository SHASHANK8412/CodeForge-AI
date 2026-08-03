"""
AIForge V2 — Day 13 Hybrid Retriever & Fast Path Engine
Combines Vector, Keyword (BM25/FTS), Symbol (Day 11), and Structural Search with
Reciprocal Rank Fusion (RRF), Score Normalization, Deduplication, and Deterministic Fast Paths.
"""
import re
import math
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

from backend.rag.models import (
    RetrievalDomain,
    ChunkRecord,
    RetrievalCandidate,
    RetrievalDecision,
    QueryType
)
from backend.rag.config import global_rag_config
from backend.rag.ingestion import global_ingestion_pipeline, DocumentIngestionPipeline
from backend.rag.embedding_service import global_embedding_service, cosine_similarity
from backend.repository.indexer import global_repository_indexer

logger = logging.getLogger("aiforge.rag.hybrid_retriever")


class HybridRetriever:
    """
    HybridRetriever executes multi-modal retrieval across Vector, Lexical, Symbol, and Structural channels.
    Includes deterministic Fast-Paths and Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, ingestion_pipeline: Optional[DocumentIngestionPipeline] = None):
        self.ingestion_pipeline = ingestion_pipeline or global_ingestion_pipeline
        self.embedding_service = global_embedding_service
        self.indexer = global_repository_indexer

    def retrieve(
        self,
        query: str,
        decision: RetrievalDecision,
        top_k: int = 20
    ) -> List[RetrievalCandidate]:
        if not decision.required or not decision.domains:
            return []

        # 1. Check Deterministic Fast-Paths
        fast_path_candidates = self._check_fast_paths(query, decision)
        if fast_path_candidates:
            logger.info(f"HybridRetriever: Resolved query via Fast-Path ({len(fast_path_candidates)} candidate(s))")
            return fast_path_candidates

        all_candidates: List[RetrievalCandidate] = []
        all_chunks = list(self.ingestion_pipeline.chunks.values())

        domain_chunks = all_chunks

        if not domain_chunks:
            logger.info("HybridRetriever: No ingested chunks available for search.")
            return []

        # 2. Channel 1: Vector Search (Semantic)
        vector_candidates = self._vector_search(query, domain_chunks, top_k=top_k)

        # 3. Channel 2: Keyword Search (Lexical / BM25 token match)
        keyword_candidates = self._keyword_search(query, domain_chunks, top_k=top_k)

        # 4. Channel 3: Symbol Search (Day 11 Symbol Index)
        symbol_candidates = self._symbol_search(query, decision, domain_chunks)

        # 5. Channel 4: Structural Search (Routes, Files, Dependencies)
        structural_candidates = self._structural_search(query, decision, domain_chunks)

        # 6. Reciprocal Rank Fusion (RRF) & Deduplication
        fused = self._reciprocal_rank_fusion(
            [vector_candidates, keyword_candidates, symbol_candidates, structural_candidates],
            rrf_k=60
        )

        # 7. Near-Duplicate Reduction
        deduped = self._reduce_near_duplicates(fused)

        logger.info(f"HybridRetriever: Fused {len(vector_candidates)} vector, {len(keyword_candidates)} keyword, "
                    f"{len(symbol_candidates)} symbol, {len(structural_candidates)} structural candidates -> {len(deduped)} final candidates.")

        return deduped[:top_k]

    # --- Fast-Path Implementations ---
    def _check_fast_paths(self, query: str, decision: RetrievalDecision) -> List[RetrievalCandidate]:
        candidates: List[RetrievalCandidate] = []
        q_lower = query.lower()

        # Fast Path 1: Exact File Path Match
        for f in decision.target_files:
            matching_chunks = [c for c in self.ingestion_pipeline.chunks.values() if c.path and f.lower() in c.path.lower()]
            for mc in matching_chunks:
                candidates.append(RetrievalCandidate(
                    chunk_id=mc.chunk_id,
                    source_id=mc.source_id,
                    domain=mc.domain,
                    score=1.0,
                    retrieval_method="fast_path_filepath",
                    text=mc.text,
                    metadata=mc.metadata
                ))
        if candidates:
            return candidates

        # Fast Path 2: Exact Symbol Match
        for sym in decision.target_symbols:
            matching_chunks = [c for c in self.ingestion_pipeline.chunks.values() if c.symbol and sym.lower() == c.symbol.lower()]
            for mc in matching_chunks:
                candidates.append(RetrievalCandidate(
                    chunk_id=mc.chunk_id,
                    source_id=mc.source_id,
                    domain=mc.domain,
                    score=0.98,
                    retrieval_method="fast_path_symbol",
                    text=mc.text,
                    metadata=mc.metadata
                ))
        if candidates:
            return candidates

        # Fast Path 3: Exact Route Match (e.g. "POST /login")
        route_match = re.search(r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/[a-zA-Z0-9_\-/]+)", query, re.IGNORECASE)
        if route_match:
            method, endpoint = route_match.group(1).upper(), route_match.group(2).lower()
            for c in self.ingestion_pipeline.chunks.values():
                if endpoint in c.text.lower() or method in c.text:
                    candidates.append(RetrievalCandidate(
                        chunk_id=c.chunk_id,
                        source_id=c.source_id,
                        domain=c.domain,
                        score=0.95,
                        retrieval_method="fast_path_route",
                        text=c.text,
                        metadata=c.metadata
                    ))
            if candidates:
                return candidates

        # Fast Path 4: Quoted Error String Match
        quoted_errors = re.findall(r'"([^"]{6,})"', query)
        for err in quoted_errors:
            for c in self.ingestion_pipeline.chunks.values():
                if err.lower() in c.text.lower():
                    candidates.append(RetrievalCandidate(
                        chunk_id=c.chunk_id,
                        source_id=c.source_id,
                        domain=c.domain,
                        score=0.96,
                        retrieval_method="fast_path_error",
                        text=c.text,
                        metadata=c.metadata
                    ))

        return candidates

    # --- Channel Search Methods ---
    def _vector_search(self, query: str, chunks: List[ChunkRecord], top_k: int) -> List[RetrievalCandidate]:
        q_vector = self.embedding_service.get_embedding(query)
        scored: List[Tuple[ChunkRecord, float]] = []

        for c in chunks:
            c_vec = c.metadata.get("embedding")
            if c_vec:
                sim = cosine_similarity(q_vector, c_vec)
                scored.append((c, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for c, score in scored[:top_k]:
            results.append(RetrievalCandidate(
                chunk_id=c.chunk_id,
                source_id=c.source_id,
                domain=c.domain,
                score=round(score, 4),
                retrieval_method="vector",
                text=c.text,
                metadata=c.metadata
            ))
        return results

    def _keyword_search(self, query: str, chunks: List[ChunkRecord], top_k: int) -> List[RetrievalCandidate]:
        q_tokens = set(re.findall(r"\w+", query.lower()))
        if not q_tokens:
            return []

        scored: List[Tuple[ChunkRecord, float]] = []
        for c in chunks:
            c_text_lower = c.text.lower()
            matches = sum(1 for t in q_tokens if t in c_text_lower)
            if matches > 0:
                score = matches / math.sqrt(len(q_tokens) * len(c.text.split()))
                scored.append((c, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for c, score in scored[:top_k]:
            results.append(RetrievalCandidate(
                chunk_id=c.chunk_id,
                source_id=c.source_id,
                domain=c.domain,
                score=round(min(score * 2.0, 1.0), 4),
                retrieval_method="keyword",
                text=c.text,
                metadata=c.metadata
            ))
        return results

    def _symbol_search(self, query: str, decision: RetrievalDecision, chunks: List[ChunkRecord]) -> List[RetrievalCandidate]:
        results: List[RetrievalCandidate] = []
        for sym in decision.target_symbols:
            for c in chunks:
                if c.symbol and sym.lower() in c.symbol.lower():
                    results.append(RetrievalCandidate(
                        chunk_id=c.chunk_id,
                        source_id=c.source_id,
                        domain=c.domain,
                        score=0.90,
                        retrieval_method="symbol",
                        text=c.text,
                        metadata=c.metadata
                    ))
        return results

    def _structural_search(self, query: str, decision: RetrievalDecision, chunks: List[ChunkRecord]) -> List[RetrievalCandidate]:
        results: List[RetrievalCandidate] = []
        for f in decision.target_files:
            for c in chunks:
                if c.path and f.lower() in c.path.lower():
                    results.append(RetrievalCandidate(
                        chunk_id=c.chunk_id,
                        source_id=c.source_id,
                        domain=c.domain,
                        score=0.88,
                        retrieval_method="structural",
                        text=c.text,
                        metadata=c.metadata
                    ))
        return results

    # --- Fusion & Deduplication ---
    def _reciprocal_rank_fusion(self, candidate_lists: List[List[RetrievalCandidate]], rrf_k: int = 60) -> List[RetrievalCandidate]:
        scores: Dict[str, float] = {}
        candidate_map: Dict[str, RetrievalCandidate] = {}

        for clist in candidate_lists:
            for rank, cand in enumerate(clist):
                cid = cand.chunk_id
                candidate_map[cid] = cand
                rrf_score = 1.0 / (rrf_k + rank + 1)
                scores[cid] = scores.get(cid, 0.0) + rrf_score

        sorted_cids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
        fused = []
        max_score = scores[sorted_cids[0]] if sorted_cids else 1.0

        for cid in sorted_cids:
            cand = candidate_map[cid]
            cand.score = round(scores[cid] / max_score, 4)
            fused.append(cand)

        return fused

    def _reduce_near_duplicates(self, candidates: List[RetrievalCandidate]) -> List[RetrievalCandidate]:
        deduped: List[RetrievalCandidate] = []
        seen_texts: List[set] = []

        for cand in candidates:
            tokens = set(cand.text.lower().split())
            if not tokens:
                continue

            is_dup = False
            for st in seen_texts:
                inter = len(tokens.intersection(st))
                union = len(tokens.union(st))
                jaccard = inter / union if union > 0 else 0.0
                if jaccard > 0.85:
                    is_dup = True
                    break

            if not is_dup:
                seen_texts.append(tokens)
                deduped.append(cand)

        return deduped


# Global Hybrid Retriever Singleton
global_hybrid_retriever = HybridRetriever()
