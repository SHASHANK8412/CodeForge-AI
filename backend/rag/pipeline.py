"""
AIForge V2 — Day 13 Integrated Production RAG Pipeline
Orchestrates DocumentIngestionPipeline, HybridRetriever, QueryEngine, Reranker,
ContextSelector, and GroundingValidator into a unified production interface.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.rag.models import (
    RetrievalDomain,
    GroundingContext,
    GroundedResponse,
    GroundingStatus
)
from backend.rag.config import global_rag_config
from backend.rag.ingestion import global_ingestion_pipeline, DocumentIngestionPipeline
from backend.rag.query_engine import global_decision_engine, RetrievalDecisionEngine
from backend.rag.hybrid_retriever import global_hybrid_retriever, HybridRetriever
from backend.rag.reranker import global_reranker, Reranker
from backend.rag.context_selector import global_context_selector, ContextSelector
from backend.rag.grounding import global_grounding_validator, global_citation_validator, EvidenceComparator
from backend.rag.agent_mixin import RetrievalAwareAgentMixin

logger = logging.getLogger("aiforge.rag.pipeline")


class RAGPipeline(RetrievalAwareAgentMixin):
    """
    Production-Grade RAG Pipeline for Day 13:
    Ingestion -> Decision Engine -> Hybrid Retriever -> Reranker -> Context Selector -> Grounded Prompting -> Citation/Grounding Validator
    """

    def __init__(self):
        self.ingestion = global_ingestion_pipeline
        self.decision_engine = global_decision_engine
        self.hybrid_retriever = global_hybrid_retriever
        self.reranker = global_reranker
        self.context_selector = global_context_selector
        self.grounding_validator = global_grounding_validator
        self.citation_validator = global_citation_validator
        self.evidence_comparator = EvidenceComparator()

    def process_and_index_document(
        self,
        filepath: str,
        domain: RetrievalDomain = RetrievalDomain.DOCUMENT,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: str = "default_project"
    ) -> Dict[str, Any]:
        """Loads, structure-chunks, redacts secrets, embeds, and indexes document under project_id."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        meta = metadata or {}
        meta["project_id"] = project_id

        content = path.read_text(encoding="utf-8", errors="ignore")
        source_rec, chunk_recs = self.ingestion.ingest_document(
            filepath_or_name=path.name,
            content=content,
            domain=domain,
            metadata=meta
        )

        # Index into vector_store with project_id
        from backend.rag.splitter import global_text_splitter
        from backend.rag.embedding_service import global_embedding_service
        from backend.rag.vector_store import global_vector_store

        raw_chunks = global_text_splitter.split_markdown(content, path.name) if path.suffix.lower() == ".md" else global_text_splitter.split_text(content)
        chunk_dicts = []
        embeddings = []
        for idx, c_dict in enumerate(raw_chunks):
            c_text = c_dict if isinstance(c_dict, str) else c_dict.get("text", "")
            chunk_dicts.append({
                "id": f"{project_id}_{path.name}_chunk_{idx}",
                "text": c_text,
                "source": path.name,
                "heading": c_dict.get("heading", "") if isinstance(c_dict, dict) else "",
                "document_type": meta.get("document_type", "DOCUMENTATION")
            })
            embeddings.append(global_embedding_service.embed_document(c_text))

        global_vector_store.add_documents(chunk_dicts, embeddings, project_id=project_id)

        return {
            "filename": path.name,
            "project_id": project_id,
            "source_id": source_rec.source_id,
            "chunks_count": len(chunk_recs),
            "status": "success"
        }

    def retrieve_context(self, query: str, top_k: int = 5, project_id: str = "default_project") -> List[Dict[str, Any]]:
        """Backwards compatible top_k context retrieval for project_id."""
        decision = self.decision_engine.analyze(query, has_documents=bool(self.ingestion.sources))
        if not decision.required:
            return []

        candidates = self.hybrid_retriever.retrieve(query, decision, top_k=top_k * 2, project_id=project_id)
        reranked = self.reranker.rerank(candidates, query, decision, top_k=top_k)

        results = []
        for c in reranked:
            results.append({
                "id": c.chunk_id,
                "project_id": getattr(c, "project_id", project_id),
                "text": c.text,
                "source": c.metadata.get("source") or c.metadata.get("path") or c.source_id,
                "score": c.score,
                "domain": c.domain.value,
                "retrieval_method": c.retrieval_method
            })
        return results

    def query_grounded_answer(
        self,
        query: str,
        active_repo_files: Optional[List[str]] = None,
        has_documents: bool = False,
        conversation_context: str = ""
    ) -> GroundedResponse:
        """Executes full end-to-end grounded RAG answer generation & validation."""
        decision, grounding_ctx, prompt_ctx = self.process_with_rag(
            agent_name="RAGPipeline",
            user_query=query,
            active_repo_files=active_repo_files,
            has_documents=has_documents,
            conversation_context=conversation_context
        )

        if not decision.required:
            return GroundedResponse(
                answer="No retrieval required for this query.",
                citations=[],
                unsupported_claims=[],
                grounding_status=GroundingStatus.NOT_APPLICABLE,
                confidence_score=1.0
            )

        if not grounding_ctx.chunks:
            return GroundedResponse(
                answer="I couldn't find evidence in the available sources matching your question.",
                citations=[],
                unsupported_claims=[],
                grounding_status=GroundingStatus.INSUFFICIENT_EVIDENCE,
                confidence_score=1.0,
                evidence_summary="No candidates met the minimum relevance threshold."
            )

        # Generate Grounded Response Snippets
        snippets = []
        for cid, label in grounding_ctx.source_labels.items():
            chk = next((c for c in grounding_ctx.chunks if c.chunk_id == cid), None)
            if chk:
                snippets.append(f"{label} {chk.path or chk.metadata.get('source') or chk.source_id}:\n  {chk.text[:300]}")

        raw_answer = f"According to indexed sources:\n\n" + "\n\n".join(snippets)
        return self.validate_and_format_response(raw_answer, grounding_ctx)

    def get_context_string_for_agent(self, agent_name: str, query: str = "", project_id: str = "default_project") -> str:
        """Retrieves and formats RAG context string for a specific agent step and project_id."""
        try:
            chunks = self.retrieve_context(query or f"Best practices for {agent_name}", top_k=3, project_id=project_id)
            if not chunks:
                return f"[RAG Context for {agent_name}]: No domain documentation indexed."
            snippets = [f"- {c['source']}: {c['text'][:250]}" for c in chunks]
            return f"[RAG Context for {agent_name}]:\n" + "\n".join(snippets)
        except Exception as e:
            logger.warning(f"get_context_string_for_agent failed safely: {e}")
            return f"[RAG Context for {agent_name}]: N/A"

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on ingested sources and chunks."""
        return {
            "total_sources": len(self.ingestion.sources),
            "total_chunks": len(self.ingestion.chunks),
            "sources": [s.name for s in self.ingestion.sources.values()]
        }


# Global RAG Pipeline Instance
global_rag_pipeline = RAGPipeline()

