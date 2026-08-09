"""
AIForge V2 — Day 13 Centralized RAG Configuration & Feature Flags
"""
import os
from typing import Dict, Any
from pydantic import BaseModel


class RAGConfig(BaseModel):
    # Feature Flags
    AIFORGE_RAG_ENABLED: bool = True
    AIFORGE_HYBRID_RETRIEVAL_ENABLED: bool = True
    AIFORGE_RERANK_ENABLED: bool = True
    AIFORGE_GROUNDING_VALIDATION_ENABLED: bool = True
    AIFORGE_CITATIONS_ENABLED: bool = True
    AIFORGE_QUERY_REWRITE_ENABLED: bool = True
    AIFORGE_RAG_CACHE_ENABLED: bool = True

    # Retrieval Tuning Parameters
    RAG_CHUNK_TARGET_TOKENS: int = 300
    RAG_CHUNK_OVERLAP_TOKENS: int = 50
    CANDIDATE_K: int = 20
    RERANK_K: int = 10
    SELECTED_K: int = 5
    MIN_RETRIEVAL_RELEVANCE: float = 0.20
    MAX_QUERY_VARIANTS: int = 3
    MAX_SUBQUERIES: int = 3
    CACHE_TTL_SECONDS: int = 3600

    @classmethod
    def from_env(cls) -> "RAGConfig":
        return cls(
            AIFORGE_RAG_ENABLED=os.getenv("AIFORGE_RAG_ENABLED", "true").lower() == "true",
            AIFORGE_HYBRID_RETRIEVAL_ENABLED=os.getenv("AIFORGE_HYBRID_RETRIEVAL_ENABLED", "true").lower() == "true",
            AIFORGE_RERANK_ENABLED=os.getenv("AIFORGE_RERANK_ENABLED", "true").lower() == "true",
            AIFORGE_GROUNDING_VALIDATION_ENABLED=os.getenv("AIFORGE_GROUNDING_VALIDATION_ENABLED", "true").lower() == "true",
            AIFORGE_CITATIONS_ENABLED=os.getenv("AIFORGE_CITATIONS_ENABLED", "true").lower() == "true",
            AIFORGE_QUERY_REWRITE_ENABLED=os.getenv("AIFORGE_QUERY_REWRITE_ENABLED", "true").lower() == "true",
            AIFORGE_RAG_CACHE_ENABLED=os.getenv("AIFORGE_RAG_CACHE_ENABLED", "true").lower() == "true",
        )


# Global RAG Config Singleton
global_rag_config = RAGConfig.from_env()
