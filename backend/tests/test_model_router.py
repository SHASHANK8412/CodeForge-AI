"""
AIForge Day 3 Model Router Unit Test Suite
==========================================
Fast unit tests for ModelRouter without requiring LLM generation calls.
Tests generation profiles, intent-to-profile mapping, capability matching,
single-model installations, fallback chains, and env variable overrides.
"""

import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.models.model_router import (
    ModelRouter,
    GenerationProfile,
    ModelSelection,
    PROFILES,
    get_model_capabilities,
    discover_installed_models,
)


class TestModelRouterUnit(unittest.TestCase):
    """Step 21: Model Router Unit Tests (Mocked LLM discovery)."""

    def setUp(self):
        self.router = ModelRouter()

    @patch("backend.models.model_router.discover_installed_models")
    def test_explanation_intent_routes_to_general_model(self, mock_discover):
        mock_discover.return_value = ["qwen2.5-coder:latest", "qwen2.5:latest"]
        res = self.router.select("EXPLANATION", agent_name="ExplanationAgent")

        self.assertEqual(res.profile.name, "EXPLANATION")
        self.assertEqual(res.selected_model, "qwen2.5:latest")
        self.assertEqual(res.temperature, 0.4)
        self.assertIn("qwen2.5-coder:latest", res.fallback_models)

    @patch("backend.models.model_router.discover_installed_models")
    def test_coding_intent_routes_to_coder_model(self, mock_discover):
        mock_discover.return_value = ["qwen2.5-coder:latest", "qwen2.5:latest"]
        res = self.router.select("CODING", agent_name="CodingAgent")

        self.assertEqual(res.profile.name, "CODING")
        self.assertEqual(res.selected_model, "qwen2.5-coder:latest")
        self.assertEqual(res.temperature, 0.1)
        self.assertEqual(res.num_predict, 2500)
        self.assertIn("qwen2.5:latest", res.fallback_models)

    @patch("backend.models.model_router.discover_installed_models")
    def test_debugging_intent_routes_to_coder_model(self, mock_discover):
        mock_discover.return_value = ["qwen2.5-coder:latest", "qwen2.5:latest"]
        res = self.router.select("DEBUGGING", agent_name="DebugAgent")

        self.assertEqual(res.profile.name, "DEBUGGING")
        self.assertEqual(res.selected_model, "qwen2.5-coder:latest")
        self.assertEqual(res.temperature, 0.0)

    @patch("backend.models.model_router.discover_installed_models")
    def test_general_qa_and_unknown_use_general_model(self, mock_discover):
        mock_discover.return_value = ["qwen2.5-coder:latest", "qwen2.5:latest"]

        res_general = self.router.select("GENERAL_QA", agent_name="ExplanationAgent")
        self.assertEqual(res_general.profile.name, "GENERAL")
        self.assertEqual(res_general.selected_model, "qwen2.5:latest")

        # UNKNOWN must NOT default to coder model!
        res_unknown = self.router.select("UNKNOWN", agent_name="ClarificationAgent")
        self.assertEqual(res_unknown.profile.name, "GENERAL")
        self.assertEqual(res_unknown.selected_model, "qwen2.5:latest")

    @patch("backend.models.model_router.discover_installed_models")
    def test_rag_and_resume_profiles(self, mock_discover):
        mock_discover.return_value = ["qwen2.5-coder:latest", "qwen2.5:latest"]

        res_rag = self.router.select("RAG_QUERY", agent_name="RAGAgent")
        self.assertEqual(res_rag.profile.name, "RAG")
        self.assertEqual(res_rag.selected_model, "qwen2.5:latest")
        self.assertEqual(res_rag.temperature, 0.1)

        res_resume = self.router.select("RESUME", agent_name="ResumeAgent")
        self.assertEqual(res_resume.profile.name, "RESUME")
        self.assertEqual(res_resume.selected_model, "qwen2.5:latest")

    @patch("backend.models.model_router.discover_installed_models")
    def test_project_generation_agent_roles(self, mock_discover):
        mock_discover.return_value = ["qwen2.5-coder:latest", "qwen2.5:latest"]

        # Planner -> PLANNING (general model)
        res_planner = self.router.select("PROJECT_GENERATION", agent_name="PlannerAgent")
        self.assertEqual(res_planner.profile.name, "PLANNING")
        self.assertEqual(res_planner.selected_model, "qwen2.5:latest")

        # Architect -> ARCHITECTURE (coder model)
        res_arch = self.router.select("PROJECT_GENERATION", agent_name="ArchitectAgent")
        self.assertEqual(res_arch.profile.name, "ARCHITECTURE")
        self.assertEqual(res_arch.selected_model, "qwen2.5-coder:latest")

        # Backend -> CODING (coder model)
        res_back = self.router.select("PROJECT_GENERATION", agent_name="BackendAgent")
        self.assertEqual(res_back.profile.name, "CODING")
        self.assertEqual(res_back.selected_model, "qwen2.5-coder:latest")

        # Reviewer -> REVIEW (coder model)
        res_rev = self.router.select("PROJECT_GENERATION", agent_name="ReviewerAgent")
        self.assertEqual(res_rev.profile.name, "REVIEW")
        self.assertEqual(res_rev.selected_model, "qwen2.5-coder:latest")

        # Documentation -> DOCUMENTATION (general model)
        res_doc = self.router.select("PROJECT_GENERATION", agent_name="DocumentationAgent")
        self.assertEqual(res_doc.profile.name, "DOCUMENTATION")
        self.assertEqual(res_doc.selected_model, "qwen2.5:latest")

    @patch("backend.models.model_router.discover_installed_models")
    def test_single_model_installation_fallback(self, mock_discover):
        # Only one model installed (Step 19)
        mock_discover.return_value = ["only-one-model:latest"]

        res_exp = self.router.select("EXPLANATION", agent_name="ExplanationAgent")
        self.assertEqual(res_exp.selected_model, "only-one-model:latest")
        self.assertEqual(res_exp.profile.name, "EXPLANATION")
        self.assertEqual(res_exp.temperature, 0.4)

        res_code = self.router.select("CODING", agent_name="CodingAgent")
        self.assertEqual(res_code.selected_model, "only-one-model:latest")
        self.assertEqual(res_code.profile.name, "CODING")
        self.assertEqual(res_code.temperature, 0.1)

    @patch("backend.models.model_router.discover_installed_models")
    def test_env_variable_overrides(self, mock_discover):
        mock_discover.return_value = ["custom-gen:latest", "qwen2.5-coder:latest"]
        os.environ["AIFORGE_GENERAL_MODEL"] = "custom-gen"

        try:
            res = self.router.select("EXPLANATION", agent_name="ExplanationAgent")
            self.assertEqual(res.selected_model, "custom-gen:latest")
        finally:
            os.environ.pop("AIFORGE_GENERAL_MODEL", None)


if __name__ == "__main__":
    unittest.main()
