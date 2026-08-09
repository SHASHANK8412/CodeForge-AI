"""
AIForge V2 — Day 13 Query Analysis, Decision Engine & Query Rewriter
Determines retrieval necessity, classifies query intent, resolves follow-up references,
and generates query variants for multi-hop searches.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

from backend.rag.models import (
    RetrievalDomain,
    QueryType,
    RetrievalDecision
)
from backend.rag.config import global_rag_config

logger = logging.getLogger("aiforge.rag.query_engine")

# Patterns for queries that NEVER require RAG
GENERIC_QA_PATTERNS = [
    r"explain formula 1",
    r"write binary search",
    r"palindrome",
    r"fibonacci",
    r"bubble sort",
    r"what is python",
    r"hello",
    r"who are you",
    r"tell me a joke",
    r"solve \d+",
    r"convert \w+ to \w+",
]

# Patterns triggering REPOSITORY retrieval
REPO_QUERY_PATTERNS = [
    r"this repo",
    r"repository",
    r"codebase",
    r"in auth_service",
    r"in backend",
    r"implemented",
    r"defined in",
    r"where is",
    r"how does .* work",
    r"fix function",
    r"endpoint",
    r"route",
    r"\.py",
    r"\.js",
    r"\.ts",
]

# Patterns triggering DOCUMENT retrieval
DOC_QUERY_PATTERNS = [
    r"pdf",
    r"document",
    r"according to",
    r"architecture\.md",
    r"prd",
    r"specification",
    r"eligibility",
    r"requirements",
    r"spec",
    r"\.pdf",
    r"\.docx",
]


class RetrievalDecisionEngine:
    """
    RetrievalDecisionEngine decides whether a user query requires retrieval,
    identifies domains, extracts explicit file/symbol targets, and classifies query type.
    """

    def analyze(
        self,
        query: str,
        active_repo_files: Optional[List[str]] = None,
        has_documents: bool = False,
        conversation_context: str = ""
    ) -> RetrievalDecision:
        if not query or not query.strip():
            return RetrievalDecision(
                required=False,
                domains=[],
                reason="Empty query",
                query_type=QueryType.FACT_LOOKUP
            )

        q_lower = query.lower().strip()

        # 1. Check for generic non-RAG patterns
        for pattern in GENERIC_QA_PATTERNS:
            if re.search(pattern, q_lower):
                logger.info(f"Retrieval Decision: NOT REQUIRED for generic query '{query[:30]}...'")
                return RetrievalDecision(
                    required=False,
                    domains=[],
                    reason=f"Generic query matched pattern: {pattern}",
                    query_type=QueryType.FACT_LOOKUP
                )

        # 2. Check for explicit domain markers
        domains: List[RetrievalDomain] = []
        is_repo_query = any(re.search(p, q_lower) for p in REPO_QUERY_PATTERNS) or bool(active_repo_files)
        is_doc_query = any(re.search(p, q_lower) for p in DOC_QUERY_PATTERNS) or has_documents

        if is_repo_query and is_doc_query:
            domains = [RetrievalDomain.REPOSITORY, RetrievalDomain.DOCUMENT]
        elif is_repo_query:
            domains = [RetrievalDomain.REPOSITORY]
        elif is_doc_query:
            domains = [RetrievalDomain.DOCUMENT]
        else:
            # If prompt asks specific codebase/document structural questions
            if "where" in q_lower or "how" in q_lower or "check" in q_lower or "match" in q_lower:
                domains = [RetrievalDomain.REPOSITORY] if active_repo_files else ([RetrievalDomain.DOCUMENT] if has_documents else [])

        if not domains:
            logger.info(f"Retrieval Decision: NOT REQUIRED (No target domains identified for '{query[:30]}...')")
            return RetrievalDecision(
                required=False,
                domains=[],
                reason="No active repository or uploaded document target identified",
                query_type=QueryType.FACT_LOOKUP
            )

        # 3. Classify Query Type
        query_type = self._classify_query_type(q_lower, domains)

        # 4. Extract Explicit File & Symbol Targets
        target_files = self._extract_file_targets(query)
        target_symbols = self._extract_symbol_targets(query)

        # 5. Build Bounded Rewritten Queries & Subqueries
        rewritten_queries = QueryRewriter().generate_variants(query, query_type, conversation_context)
        subqueries = QueryRewriter().decompose_multi_hop(query) if query_type == QueryType.MULTI_HOP else []

        decision = RetrievalDecision(
            required=True,
            domains=domains if len(domains) > 1 else domains,
            reason=f"Matched domains {[d.value for d in domains]} for {query_type.value}",
            query_type=query_type,
            rewritten_queries=rewritten_queries,
            subqueries=subqueries,
            target_files=target_files,
            target_symbols=target_symbols
        )
        logger.info(f"Retrieval Decision: REQUIRED for '{query[:30]}...' -> {[d.value for d in domains]}")
        return decision

    def _classify_query_type(self, q_lower: str, domains: List[RetrievalDomain]) -> QueryType:
        if "compare" in q_lower or "match" in q_lower or "vs" in q_lower:
            return QueryType.COMPARISON
        if "summarize" in q_lower or "overview" in q_lower or "all" in q_lower:
            return QueryType.SUMMARY
        if "and" in q_lower and ("how" in q_lower or "verify" in q_lower) and len(q_lower.split()) > 10:
            return QueryType.MULTI_HOP
        if "fix" in q_lower or "bug" in q_lower or "error" in q_lower or "fail" in q_lower:
            return QueryType.DEBUG_CONTEXT
        if "where is" in q_lower or "defined" in q_lower or "function" in q_lower or "class" in q_lower:
            return QueryType.CODE_SEARCH
        if RetrievalDomain.REPOSITORY in domains:
            return QueryType.IMPLEMENTATION_CONTEXT
        return QueryType.FACT_LOOKUP

    def _extract_file_targets(self, query: str) -> List[str]:
        # Matches filename paths like backend/routes/auth.py or architecture.pdf
        return re.findall(r"\b[a-zA-Z0-9_\-\/]+\.(?:py|js|ts|json|md|pdf|docx|txt)\b", query)

    def _extract_symbol_targets(self, query: str) -> List[str]:
        # Matches snake_case or camelCase function/class identifiers
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", query)
        targets = []
        for w in words:
            if "_" in w or (any(c.isupper() for c in w) and any(c.islower() for c in w)):
                if w.lower() not in {"where", "is", "defined", "this", "function", "implemented"}:
                    targets.append(w)
        return targets


class QueryRewriter:
    """
    QueryRewriter resolves ambiguous pronoun references from conversation context,
    decomposes multi-hop queries, and generates bounded search query variants.
    """

    def generate_variants(self, query: str, query_type: QueryType, conversation_context: str = "") -> List[str]:
        if not global_rag_config.AIFORGE_QUERY_REWRITE_ENABLED:
            return [query]

        resolved = self.resolve_follow_up(query, conversation_context)
        variants = [resolved]

        # Generate synonym / alternative variants
        if "auth" in resolved.lower() or "token" in resolved.lower():
            variants.append(resolved.replace("auth", "authentication").replace("token", "JWT access refresh token"))
        elif "db" in resolved.lower() or "database" in resolved.lower():
            variants.append(resolved.replace("db", "database model schema"))

        return list(dict.fromkeys(variants))[:global_rag_config.MAX_QUERY_VARIANTS]

    def resolve_follow_up(self, query: str, conversation_context: str) -> str:
        """Resolves pronouns like 'it', 'that function', 'the route' using conversation context."""
        if not conversation_context:
            return query

        q_lower = query.lower()
        if "where is it" in q_lower or "how is it" in q_lower or "explain it" in q_lower:
            # Extract last mentioned entity from conversation context
            ctx_lower = conversation_context.lower()
            if "authentication" in ctx_lower or "auth" in ctx_lower or "token" in ctx_lower:
                return query.replace("it", "authentication token validation")
            elif "database" in ctx_lower or "redis" in ctx_lower:
                return query.replace("it", "database redis connection")

        return query

    def decompose_multi_hop(self, query: str) -> List[str]:
        """Decomposes multi-part questions into bounded subqueries."""
        subqueries = []
        # Split on 'and', 'then', or commas
        parts = re.split(r"\b(?:and|then)\b|,", query, flags=re.IGNORECASE)
        for p in parts:
            p_clean = p.strip()
            if len(p_clean) > 5:
                subqueries.append(p_clean)
        return subqueries[:global_rag_config.MAX_SUBQUERIES]


# Global Decision Engine Singleton
global_decision_engine = RetrievalDecisionEngine()
