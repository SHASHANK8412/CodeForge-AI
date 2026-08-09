"""
AIForge V2 — Day 13 Retrieval & Grounding Evaluation Engine
Computes empirical metrics: Recall@K, Precision@K, MRR, nDCG@5, Citation Accuracy,
Grounded Answer Rate, Unsupported Claim Rate, No-Answer Accuracy, and Latency breakdowns.
"""
import math
import time
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

from backend.rag.models import (
    GroundingContext,
    GroundedResponse,
    GroundingStatus,
    RetrievalCandidate
)

logger = logging.getLogger("aiforge.rag.evaluator")


class RetrievalEvaluator:
    """Computes Recall@K, Precision@K, MRR, nDCG@5, Hit Rate for retrieval candidates."""

    def evaluate_retrieval(
        self,
        retrieved_candidates: List[RetrievalCandidate],
        expected_chunk_ids: List[str],
        k: int = 5
    ) -> Dict[str, float]:
        if not expected_chunk_ids:
            return {"recall_at_k": 1.0, "precision_at_k": 1.0, "mrr": 1.0, "ndcg_at_k": 1.0, "hit_rate": 1.0}

        retrieved_k = retrieved_candidates[:k]
        hits = 0
        hit_ranks = []

        for rank, c in enumerate(retrieved_k, 1):
            c_src = (c.metadata.get("source") or c.metadata.get("path") or c.source_id).lower()
            matched = False
            for exp in expected_chunk_ids:
                exp_lower = exp.lower()
                exp_base = exp_lower.split("_chunk")[0].replace(".pdf", "").replace(".txt", "").replace(".md", "").replace(".docx", "").replace("repo_", "").strip()
                c_base = c_src.replace(".pdf", "").replace(".txt", "").replace(".md", "").replace(".docx", "").strip()
                if exp_lower == c.chunk_id.lower() or exp_lower in c.chunk_id.lower() or (exp_base and exp_base in c_base) or (c_base and c_base in exp_base):
                    matched = True
                    break
            if matched:
                hits += 1
                hit_ranks.append(rank)

        recall = min(hits / len(expected_chunk_ids), 1.0) if expected_chunk_ids else 1.0
        precision = hits / k if k > 0 else 0.0
        hit_rate = 1.0 if hits > 0 else 0.0

        mrr = 1.0 / hit_ranks[0] if hit_ranks else 0.0

        # Compute nDCG@K
        dcg = 0.0
        for rank, c in enumerate(retrieved_k, 1):
            rel = 1.0 if rank in hit_ranks else 0.0
            dcg += rel / math.log2(rank + 1)

        idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(len(expected_chunk_ids), k) + 1))
        ndcg = dcg / idcg if idcg > 0 else 0.0

        return {
            "recall_at_k": round(recall, 4),
            "precision_at_k": round(precision, 4),
            "mrr": round(mrr, 4),
            "ndcg_at_k": round(ndcg, 4),
            "hit_rate": round(hit_rate, 4)
        }


class GroundingEvaluator:
    """Computes Grounded Answer Rate, Unsupported Claim Rate, Citation Accuracy, No-Answer Accuracy."""

    def evaluate_grounding(
        self,
        responses: List[Tuple[GroundedResponse, Dict[str, Any]]]  # (response, expected_eval_item)
    ) -> Dict[str, float]:
        if not responses:
            return {}

        total = len(responses)
        grounded_count = 0
        total_claims = 0
        unsupported_count = 0
        citation_correct = 0
        citation_total = 0
        no_answer_correct = 0
        no_answer_total = 0
        conflict_detected = 0
        conflict_total = 0

        for resp, expected in responses:
            is_expected_no_answer = expected.get("expected_no_answer") and resp.grounding_status == GroundingStatus.INSUFFICIENT_EVIDENCE
            is_expected_conflict = expected.get("expected_conflict") and resp.grounding_status == GroundingStatus.CONFLICTING_EVIDENCE

            if resp.grounding_status in (GroundingStatus.GROUNDED, GroundingStatus.NOT_APPLICABLE) or is_expected_no_answer or is_expected_conflict:
                grounded_count += 1

            unsupported_count += len(resp.unsupported_claims)

            if expected.get("expected_no_answer"):
                no_answer_total += 1
                if resp.grounding_status == GroundingStatus.INSUFFICIENT_EVIDENCE or "couldn't find evidence" in resp.answer.lower():
                    no_answer_correct += 1

            if expected.get("expected_conflict"):
                conflict_total += 1
                if resp.grounding_status == GroundingStatus.CONFLICTING_EVIDENCE or "conflict" in resp.answer.lower():
                    conflict_detected += 1

            if resp.citations:
                citation_total += len(resp.citations)
                exp_cits = expected.get("expected_citations", [])
                for cit in resp.citations:
                    if not exp_cits or any(e in cit.display or e in cit.location for e in exp_cits):
                        citation_correct += 1

        grounded_rate = grounded_count / total
        unsupported_rate = unsupported_count / total if total > 0 else 0.0
        citation_acc = citation_correct / citation_total if citation_total > 0 else 1.0
        no_answer_acc = no_answer_correct / no_answer_total if no_answer_total > 0 else 1.0
        conflict_rate = conflict_detected / conflict_total if conflict_total > 0 else 1.0

        return {
            "grounded_answer_rate": round(grounded_rate, 4),
            "unsupported_claim_rate": round(unsupported_rate, 4),
            "citation_accuracy": round(citation_acc, 4),
            "no_answer_accuracy": round(no_answer_acc, 4),
            "conflict_detection_rate": round(conflict_rate, 4)
        }


# Global Evaluator Singletons
global_retrieval_evaluator = RetrievalEvaluator()
global_grounding_evaluator = GroundingEvaluator()
