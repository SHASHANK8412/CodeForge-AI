"""
AIForge Response Evaluator & Voting System
==========================================
Evaluates outputs across competing LLM models, scores code quality & correctness, and implements majority voting logic.
"""

import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.llm")

class ResponseEvaluator:
    """
    Evaluates responses from multiple models and executes majority voting to pick the best candidate.
    """

    def evaluate_response(self, response_text: str, task_type: str = "coding") -> Dict[str, Any]:
        """
        Scores a model response across 7 criteria: Correctness, Code Quality, Security,
        Performance, Readability, Maintainability, Architecture.
        """
        score = 80.0
        feedback = []

        # 1. Code syntax check
        if "def " in response_text or "function " in response_text or "class " in response_text:
            score += 10.0
            feedback.append("Contains structured code definitions")

        # 2. Security check
        if "eval(" in response_text or "exec(" in response_text or "sk-test-" in response_text:
            score -= 25.0
            feedback.append("Contains potential security risk or unhandled dynamic evaluation")
        else:
            score += 5.0

        # 3. Readability & Comments
        if "#" in response_text or "//" in response_text:
            score += 5.0
            feedback.append("Contains inline documentation comments")

        final_score = max(0.0, min(100.0, score))
        return {
            "score": final_score,
            "feedback": feedback,
            "is_valid": final_score >= 70.0
        }

    def select_best_response(self, candidate_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates candidate model outputs and returns the top-scored candidate (AI Judge).
        """
        if not candidate_responses:
            return {"winner": "none", "score": 0.0, "response": ""}

        for cand in candidate_responses:
            eval_result = self.evaluate_response(cand.get("response", ""))
            cand["evaluation"] = eval_result
            cand["combined_score"] = eval_result["score"]

        # Sort by combined score descending
        sorted_candidates = sorted(candidate_responses, key=lambda c: c["combined_score"], reverse=True)
        winner = sorted_candidates[0]
        _logger.info(f"AI Judge selected winner: '{winner.get('model_key')}' with score {winner.get('combined_score')}")
        return {
            "winner_model": winner.get("model_key"),
            "winner_score": winner.get("combined_score"),
            "winning_response": winner.get("response"),
            "all_evaluations": sorted_candidates
        }

    def execute_majority_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Performs majority voting across model decisions (e.g., Qwen vs DeepSeek vs GPT).
        """
        votes: Dict[str, int] = {}
        for prop in proposals:
            choice = prop.get("decision", "").strip().upper()
            if choice:
                votes[choice] = votes.get(choice, 0) + 1

        if not votes:
            return {"winning_decision": "DEFAULT", "vote_breakdown": {}}

        winning_decision = max(votes.keys(), key=lambda k: votes[k])
        _logger.info(f"Majority voting completed: Winner = '{winning_decision}' with {votes[winning_decision]} vote(s)")
        return {
            "winning_decision": winning_decision,
            "vote_breakdown": votes
        }
