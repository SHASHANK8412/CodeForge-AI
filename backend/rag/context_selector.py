"""
AIForge V2 — Day 13 Context Selector & Grounding Context Builder
Selects diverse evidence candidates within token budget, assigns compact source labels ([S1], [S2]),
and builds GroundingContext object for LLM prompting and verification.
"""
import logging
from typing import Dict, Any, List, Optional

from backend.rag.models import (
    RetrievalCandidate,
    ChunkRecord,
    SourceRecord,
    GroundingContext
)
from backend.rag.config import global_rag_config
from backend.rag.ingestion import global_ingestion_pipeline

logger = logging.getLogger("aiforge.rag.context_selector")


class ContextSelector:
    """
    ContextSelector takes reranked candidates, enforces context diversity, token budgeting,
    assigns compact source labels ([S1], [S2]), and constructs the GroundingContext.
    """

    def select_context(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        max_tokens: int = 2000,
        dynamic_k: Optional[int] = None
    ) -> GroundingContext:
        if not candidates:
            return GroundingContext(
                query=query,
                sources=[],
                chunks=[],
                coverage=0.0,
                confidence_category="NONE",
                retrieval_metadata={"selected_count": 0}
            )

        k_limit = dynamic_k or global_rag_config.SELECTED_K
        selected_candidates: List[RetrievalCandidate] = []
        current_tokens = 0
        seen_sources: Dict[str, int] = {}  # source_name -> count

        for cand in candidates:
            if len(selected_candidates) >= k_limit:
                break

            s_name = cand.metadata.get("source") or cand.metadata.get("path") or cand.source_id
            # Context diversity: max 3 chunks per source
            if seen_sources.get(s_name, 0) >= 3:
                continue

            c_tokens = len(cand.text.split())
            if current_tokens + c_tokens > max_tokens and selected_candidates:
                break

            selected_candidates.append(cand)
            current_tokens += c_tokens
            seen_sources[s_name] = seen_sources.get(s_name, 0) + 1

        # Build Source Labels & Records
        source_records: List[SourceRecord] = []
        chunk_records: List[ChunkRecord] = []
        source_labels: Dict[str, str] = {}
        recorded_sources: set = set()

        for idx, cand in enumerate(selected_candidates, 1):
            s_label = f"[S{idx}]"
            source_labels[cand.chunk_id] = s_label

            src_obj = global_ingestion_pipeline.sources.get(cand.source_id)
            if src_obj and src_obj.source_id not in recorded_sources:
                source_records.append(src_obj)
                recorded_sources.add(src_obj.source_id)

            chunk_obj = global_ingestion_pipeline.chunks.get(cand.chunk_id)
            if not chunk_obj:
                # Construct inline chunk record if not in ingestion pipeline memory
                chunk_obj = ChunkRecord(
                    chunk_id=cand.chunk_id,
                    source_id=cand.source_id,
                    domain=cand.domain,
                    text=cand.text,
                    metadata=cand.metadata,
                    content_hash="",
                    path=cand.metadata.get("path"),
                    symbol=cand.metadata.get("symbol"),
                    line_start=cand.metadata.get("line_start"),
                    line_end=cand.metadata.get("line_end"),
                    page=cand.metadata.get("page"),
                    section=cand.metadata.get("section"),
                    heading=cand.metadata.get("heading")
                )
            chunk_records.append(chunk_obj)

        coverage = min(len(selected_candidates) / k_limit, 1.0)
        confidence = "HIGH" if coverage >= 0.8 else ("MEDIUM" if coverage >= 0.4 else "LOW")

        ctx = GroundingContext(
            query=query,
            sources=source_records,
            chunks=chunk_records,
            coverage=round(coverage, 2),
            confidence_category=confidence,
            retrieval_metadata={
                "selected_count": len(selected_candidates),
                "total_tokens": current_tokens,
                "top_score": selected_candidates[0].score if selected_candidates else 0.0
            },
            source_labels=source_labels
        )
        logger.info(f"ContextSelector: Selected {len(selected_candidates)} chunk(s) ({current_tokens} tokens, {confidence} confidence)")
        return ctx

    def format_grounded_prompt_context(self, context: GroundingContext) -> str:
        """Formats GroundingContext into a clean markdown evidence block with source labels [S1], [S2]."""
        if not context.chunks:
            return ""

        lines = [
            "### RETRIEVED GROUNDING EVIDENCE",
            "Use the following retrieved evidence to answer source-specific claims.",
            "Cite sources using source labels [S1], [S2] where appropriate.",
            "If the evidence does NOT support an answer, state: 'I couldn't find evidence in the available sources.'\n"
        ]

        for idx, chunk in enumerate(context.chunks, 1):
            label = f"[S{idx}]"
            src_desc = chunk.path or chunk.metadata.get("source") or chunk.source_id
            loc_desc = ""
            if chunk.line_start and chunk.line_end:
                loc_desc = f" (Lines {chunk.line_start}-{chunk.line_end})"
            elif chunk.page:
                loc_desc = f" (Page {chunk.page})"
            elif chunk.heading:
                loc_desc = f" (Section: {chunk.heading})"

            lines.append(f"**{label} Source: {src_desc}{loc_desc}**")
            lines.append(f"```\n{chunk.text}\n```\n")

        return "\n".join(lines)


# Global Context Selector Singleton
global_context_selector = ContextSelector()
