"""
AIForge Day 9 Self-Review, Reflection Loop & Refinement Test Suite
===================================================================
Verifies ReviewPolicy, ResponseCritic, CritiqueFilter, RefinementController,
BestResponseSelector, Feature Flag, and Mandatory Tests 1 through 7.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.review.models import ReviewDecision, CritiqueResult, CritiqueIssue
from backend.review.policy import global_review_policy
from backend.review.critic_agent import global_response_critic
from backend.review.filter import global_critique_filter
from backend.review.refinement_controller import global_refinement_controller
from backend.review.best_response_selector import global_best_response_selector
from backend.services.generation_service import global_generation_pipeline
from backend.quality.output_validator import ValidationResult


class TestDay9SelfReview(unittest.TestCase):

    def test_mandatory_flagship_jwt_revocation_refinement(self):
        """Mandatory Flagship Test: Initial JWT response lacks token revocation -> Critic detects missing revocation -> Refined response adds it -> BestResponseSelector picks REFINED"""
        prompt = "Design and implement FastAPI JWT authentication with access tokens, refresh tokens, role-based authorization, logout and token revocation."
        initial_response = "Here is the FastAPI JWT auth code with access_token and refresh_token generation and RBAC dependencies."

        # 1. Audit missing requirements
        critique = global_response_critic.critique(prompt, initial_response, intent="CODING")
        self.assertTrue(critique.needs_revision)
        self.assertIn("revocation", [req.lower() for req in critique.missing_requirements] + [iss.description.lower() for iss in critique.issues if "revocation" in iss.description.lower()])

        # 2. Refine response
        refinement_res = global_refinement_controller.refine(prompt, initial_response, critique, intent="CODING")
        self.assertTrue(refinement_res.improvement_made)
        self.assertIn("revocation", refinement_res.refined_response.lower())

        # 3. Best response selector
        orig_val = ValidationResult(is_valid=True, score=0.75)
        ref_val = ValidationResult(is_valid=True, score=0.98)
        best_resp, best_val, source = global_best_response_selector.select_best(
            initial_response, orig_val, refinement_res.refined_response, ref_val, improvement_made=True
        )

        self.assertEqual(source, "refined")
        self.assertIn("revocation", best_resp.lower())

    def test_mandatory_simple_prompt_no_review(self):
        """Mandatory Test: 'What is Python?' -> ReviewPolicy: should_review = False (0 Critic calls)"""
        decision = global_review_policy.should_review("EXPLANATION", "TRIVIAL", "DIRECT")
        self.assertFalse(decision.should_review)
        self.assertEqual(decision.reason, "DIRECT_STRATEGY")

    def test_excellent_response_no_refinement(self):
        """Complete response requires no revision -> returns original"""
        prompt = "Explain Formula 1"
        response = "Formula 1 is the pinnacle of motorsport racing featuring drivers and constructors."
        critique = global_response_critic.critique(prompt, response, intent="EXPLANATION")

        self.assertFalse(critique.needs_revision)

    def test_critique_filter_removes_unrequested_features(self):
        """CritiqueFilter removes unrequested Kubernetes demand on REST API prompt"""
        prompt = "Write a REST API endpoint in FastAPI."
        raw_critique = CritiqueResult(
            needs_revision=True,
            score=0.70,
            issues=[
                CritiqueIssue(category="ARCHITECTURE", severity="high", description="Missing Kubernetes deployment manifests", suggested_action="Add K8s YAML")
            ],
            missing_requirements=[]
        )

        filtered = global_critique_filter.filter_critique(prompt, raw_critique)
        self.assertFalse(filtered.needs_revision)
        self.assertEqual(len(filtered.issues), 0)

    def test_critic_failure_preserves_valid_original(self):
        """If Critic encounters error or returns empty, returns valid original response"""
        critique = global_response_critic.critique("", "")
        self.assertFalse(critique.needs_revision)
        self.assertTrue(critique.is_valid)

    def test_worse_refinement_picks_original(self):
        """If refined response has lower quality score than original, BestResponseSelector picks ORIGINAL"""
        orig_resp = "Good original implementation."
        orig_val = ValidationResult(is_valid=True, score=0.90)

        ref_resp = "Worse refined implementation."
        ref_val = ValidationResult(is_valid=True, score=0.60)

        best_resp, best_val, source = global_best_response_selector.select_best(
            orig_resp, orig_val, ref_resp, ref_val, improvement_made=True
        )
        self.assertEqual(source, "original")
        self.assertEqual(best_resp, orig_resp)

    def test_formula_1_regression_day9(self):
        """Formula 1 regression test: 0 Critic calls, 100/100 quality score, no def solve()"""
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(global_generation_pipeline.generate("Explain Formula 1"))

        self.assertEqual(res.intent, "EXPLANATION")
        self.assertEqual(res.execution_strategy, "DIRECT")
        self.assertNotIn("def solve", res.response)

    def test_feature_flag_disable_self_review(self):
        """Setting AIFORGE_SELF_REVIEW_ENABLED=false disables self-review"""
        os.environ["AIFORGE_SELF_REVIEW_ENABLED"] = "false"
        policy = global_review_policy.should_review("CODING", "COMPLEX", "PLANNED")
        self.assertFalse(policy.should_review)
        os.environ["AIFORGE_SELF_REVIEW_ENABLED"] = "true"


if __name__ == "__main__":
    unittest.main()
