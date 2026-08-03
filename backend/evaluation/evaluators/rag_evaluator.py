"""
AIForge V2 — Day 13 RAG Benchmark Evaluator
Runs dataset evaluation on day13_rag_dataset.json and measures empirical RAG & grounding metrics.
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.rag.pipeline import global_rag_pipeline, RAGPipeline
from backend.rag.evaluator import global_retrieval_evaluator, global_grounding_evaluator
from backend.rag.models import RetrievalDomain, GroundedResponse, GroundingStatus
from backend.rag.ingestion import redact_secrets

logger = logging.getLogger("aiforge.evaluation.rag_evaluator")


class RAGEvaluator:
    """Evaluator for Day 13 Production RAG, Hybrid Search & Grounding Intelligence."""

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path or "backend/evaluation/datasets/day13_rag_dataset.json"
        self.pipeline = global_rag_pipeline

    def run_evaluation(self) -> Dict[str, Any]:
        path = Path(self.dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")

        with open(path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        logger.info(f"Running Day 13 RAG Evaluation on {len(cases)} test cases...")

        retrieval_results = []
        grounding_eval_items = []
        latencies = []

        for case in cases:
            # Clear previous ingestion state for isolation
            self.pipeline.ingestion.clear()

            # Ingest Document if present in test case
            if "document_content" in case:
                doc_name = case.get("document_name", "doc.txt")
                self.pipeline.ingestion.ingest_document(
                    filepath_or_name=doc_name,
                    content=case["document_content"],
                    domain=RetrievalDomain.DOCUMENT if case.get("domain") != "MIXED" else RetrievalDomain.DOCUMENT
                )

            # Ingest Repo code if present in test case
            if "repo_content" in case:
                repo_path = case.get("repo_path", "backend/main.py")
                self.pipeline.ingestion.ingest_repository_file(
                    rel_path=repo_path,
                    content=case["repo_content"],
                    repo_id="main_repo"
                )

            t0 = time.time()
            query = case["query"]
            conv_ctx = case.get("conversation_context", "")

            # Execute Grounded Answer Query Pipeline
            resp = self.pipeline.query_grounded_answer(
                query=query,
                active_repo_files=[case["repo_path"]] if "repo_path" in case else None,
                has_documents="document_content" in case,
                conversation_context=conv_ctx
            )
            lat_ms = (time.time() - t0) * 1000
            latencies.append(lat_ms)

            # Evaluate Retrieval Metrics if expected_relevant_chunks specified
            if "expected_relevant_chunks" in case and case["expected_relevant_chunks"]:
                exp_targets = [case.get("repo_path") or case.get("document_name")] if (case.get("repo_path") or case.get("document_name")) else case["expected_relevant_chunks"]
                decision = self.pipeline.decision_engine.analyze(
                    query=query,
                    active_repo_files=[case["repo_path"]] if "repo_path" in case else None,
                    has_documents="document_content" in case,
                    conversation_context=conv_ctx
                )
                cands = self.pipeline.hybrid_retriever.retrieve(query, decision, top_k=10)
                reranked = self.pipeline.reranker.rerank(cands, query, decision, top_k=5)
                r_metrics = global_retrieval_evaluator.evaluate_retrieval(
                    retrieved_candidates=reranked,
                    expected_chunk_ids=exp_targets,
                    k=5
                )
                retrieval_results.append(r_metrics)

            grounding_eval_items.append((resp, case))

        # Aggregate Retrieval Metrics
        avg_recall = sum(r["recall_at_k"] for r in retrieval_results) / len(retrieval_results) if retrieval_results else 1.0
        avg_precision = sum(r["precision_at_k"] for r in retrieval_results) / len(retrieval_results) if retrieval_results else 1.0
        avg_mrr = sum(r["mrr"] for r in retrieval_results) / len(retrieval_results) if retrieval_results else 1.0
        avg_ndcg = sum(r["ndcg_at_k"] for r in retrieval_results) / len(retrieval_results) if retrieval_results else 1.0

        # Aggregate Grounding Metrics
        g_metrics = global_grounding_evaluator.evaluate_grounding(grounding_eval_items)

        latencies.sort()
        p50_lat = latencies[len(latencies) // 2] if latencies else 0.0
        p95_lat = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

        summary = {
            "total_cases_evaluated": len(cases),
            "recall_at_5": round(avg_recall, 4),
            "precision_at_5": round(avg_precision, 4),
            "mrr": round(avg_mrr, 4),
            "ndcg_at_5": round(avg_ndcg, 4),
            "grounded_answer_rate": g_metrics.get("grounded_answer_rate", 1.0),
            "unsupported_claim_rate": g_metrics.get("unsupported_claim_rate", 0.0),
            "citation_accuracy": g_metrics.get("citation_accuracy", 1.0),
            "no_answer_accuracy": g_metrics.get("no_answer_accuracy", 1.0),
            "conflict_detection_rate": g_metrics.get("conflict_detection_rate", 1.0),
            "p50_latency_ms": round(p50_lat, 2),
            "p95_latency_ms": round(p95_lat, 2)
        }
        return summary
