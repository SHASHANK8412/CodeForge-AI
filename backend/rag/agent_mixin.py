"""
AIForge V2 — Day 13 Retrieval-Aware Agent Mixin
Centralized mixin providing production RAG capability to all AIForge agents
without duplicating retrieval logic across agents or polluting non-RAG prompts.
"""
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from backend.rag.models import (
    RetrievalDecision,
    GroundingContext,
    GroundedResponse,
    GroundingStatus,
    RetrievalCandidate
)
from backend.rag.config import global_rag_config
from backend.rag.query_engine import global_decision_engine
from backend.rag.hybrid_retriever import global_hybrid_retriever
from backend.rag.reranker import global_reranker
from backend.rag.context_selector import global_context_selector
from backend.rag.grounding import (
    global_citation_validator,
    global_grounding_validator,
    global_evidence_comparator
)
from backend.rag.ingestion import global_ingestion_pipeline

logger = logging.getLogger("aiforge.rag.agent_mixin")


class RetrievalAwareAgentMixin:
    """
    Mixin class that equips agents with production-grade RAG, hybrid retrieval,
    reranking, grounded prompt context formatting, and citation validation.
    """

    def process_with_rag(
        self,
        agent_name: str,
        user_query: str,
        active_repo_files: Optional[List[str]] = None,
        has_documents: bool = False,
        conversation_context: str = ""
    ) -> Tuple[RetrievalDecision, GroundingContext, str]:
        """
        Executes query analysis, hybrid retrieval, reranking, and context selection.
        Returns (RetrievalDecision, GroundingContext, formatted_prompt_context).
        """
        t0 = time.time()
        if not global_rag_config.AIFORGE_RAG_ENABLED:
            logger.info(f"[{agent_name}] RAG disabled by feature flag.")
            decision = global_decision_engine.analyze(user_query)
            decision.required = False
            return decision, GroundingContext(query=user_query), ""

        # 1. Query Analysis & Decision Engine
        decision = global_decision_engine.analyze(
            query=user_query,
            active_repo_files=active_repo_files,
            has_documents=has_documents or bool(global_ingestion_pipeline.sources),
            conversation_context=conversation_context
        )

        if not decision.required:
            logger.info(f"[{agent_name}] Retrieval NOT required for query: '{user_query[:30]}...' (0 RAG Calls)")
            return decision, GroundingContext(query=user_query), ""

        # 2. Hybrid Retrieval
        candidates = global_hybrid_retriever.retrieve(
            query=user_query,
            decision=decision,
            top_k=global_rag_config.CANDIDATE_K
        )

        # 3. Candidate Reranking
        reranked = global_reranker.rerank(
            candidates=candidates,
            query=user_query,
            decision=decision,
            top_k=global_rag_config.RERANK_K
        )

        # 4. Context Selection & Grounding Context Construction
        grounding_context = global_context_selector.select_context(
            query=user_query,
            candidates=reranked,
            dynamic_k=global_rag_config.SELECTED_K
        )

        # 5. Format Grounded Evidence Prompt
        prompt_context = global_context_selector.format_grounded_prompt_context(grounding_context)

        latency_ms = round((time.time() - t0) * 1000, 2)
        logger.info(f"[{agent_name}] RAG Pipeline executed in {latency_ms}ms ({len(grounding_context.chunks)} selected chunks)")

        return decision, grounding_context, prompt_context

    def validate_and_format_response(
        self,
        raw_answer: str,
        context: GroundingContext
    ) -> GroundedResponse:
        """Validates citations and claim grounding on LLM answer."""
        if not context or not context.chunks:
            # Non-RAG or insufficient evidence
            if "couldn't find evidence" in raw_answer.lower() or "insufficient" in raw_answer.lower():
                return GroundedResponse(
                    answer=raw_answer,
                    citations=[],
                    unsupported_claims=[],
                    grounding_status=GroundingStatus.INSUFFICIENT_EVIDENCE,
                    confidence_score=1.0,
                    evidence_summary="Insufficient evidence reported cleanly."
                )
            return GroundedResponse(
                answer=raw_answer,
                citations=[],
                unsupported_claims=[],
                grounding_status=GroundingStatus.NOT_APPLICABLE,
                confidence_score=1.0
            )

        # 1. Validate Citations
        citations, invalid_cits = global_citation_validator.validate_citations(raw_answer, context)

        # 2. Validate Grounding Claims
        validation = global_grounding_validator.validate_answer(raw_answer, context)

        # 3. Grounded Refinement Loop (max 1 loop if unsupported claims exist)
        final_answer = raw_answer
        if validation.status == GroundingStatus.PARTIALLY_GROUNDED and validation.unsupported_claims:
            logger.info("RetrievalAwareAgentMixin: Unsupported claims detected -> executing 1-step grounded refinement")
            evidence_summary = "\n".join([c.text for c in context.chunks])
            refined_claims = [c for c in validation.supported_claims]
            final_answer = f"{' '.join(refined_claims)}\n\n[Note: Claims unsupported by evidence were omitted.]"
            validation.unsupported_claims = []
            validation.status = GroundingStatus.GROUNDED

        return GroundedResponse(
            answer=final_answer,
            citations=citations,
            unsupported_claims=validation.unsupported_claims,
            grounding_status=validation.status,
            confidence_score=validation.grounding_score,
            evidence_summary=validation.reason
        )
