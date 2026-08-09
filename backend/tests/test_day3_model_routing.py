"""
AIForge Day 3 End-to-End Model Routing & Performance Quality Suite
===================================================================
Tests dynamic model routing against installed Ollama models, verifying
that EXPLANATION prompts use general models, CODING/DEBUGGING prompts use
coder models, and sequential turns switch model profiles correctly.
"""

import sys
import time
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.agents.router_agent import RouterAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.models.model_router import ModelRouter, discover_installed_models
from backend.utils.response_contract import validate_response_contract


class TestDay3ModelRoutingEndToEnd(unittest.TestCase):

    def setUp(self):
        self.router = RouterAgent()
        self.model_router = ModelRouter()
        self.explanation_agent = ExplanationAgent()
        self.coding_agent = CodingAgent()
        self.debug_agent = DebugAgent()
        self.installed_models = discover_installed_models()

    def test_e2e_explain_formula_1_model_routing(self):
        prompt = "Explain Formula 1"
        intent_res = self.router.classify_intent(prompt)
        self.assertEqual(intent_res["intent"], "EXPLANATION")

        selection = self.model_router.select("EXPLANATION", agent_name="ExplanationAgent", prompt=prompt)
        self.assertEqual(selection.profile.name, "EXPLANATION")
        if "qwen2.5:latest" in self.installed_models:
            self.assertEqual(selection.selected_model, "qwen2.5:latest")

        output = self.explanation_agent.process_explanation_request(prompt)["response"]
        self.assertIn("Formula 1", output)
        self.assertNotIn("def solve", output)

        contract = validate_response_contract("EXPLANATION", prompt, output)
        self.assertTrue(contract["valid"])

    def test_e2e_explain_photosynthesis_model_routing(self):
        prompt = "Explain photosynthesis."
        intent_res = self.router.classify_intent(prompt)
        self.assertEqual(intent_res["intent"], "EXPLANATION")

        selection = self.model_router.select("EXPLANATION", agent_name="ExplanationAgent", prompt=prompt)
        self.assertEqual(selection.profile.name, "EXPLANATION")
        if "qwen2.5:latest" in self.installed_models:
            self.assertEqual(selection.selected_model, "qwen2.5:latest")

    def test_e2e_write_binary_search_model_routing(self):
        prompt = "Write binary search in Python."
        intent_res = self.router.classify_intent(prompt)
        self.assertEqual(intent_res["intent"], "CODING")

        selection = self.model_router.select("CODING", agent_name="CodingAgent", prompt=prompt)
        self.assertEqual(selection.profile.name, "CODING")
        self.assertEqual(selection.temperature, 0.1)
        if "qwen2.5-coder:latest" in self.installed_models:
            self.assertEqual(selection.selected_model, "qwen2.5-coder:latest")

    def test_e2e_debug_list_index_error_model_routing(self):
        prompt = "Fix this Python code: numbers = [1,2,3]; print(numbers[5])"
        intent_res = self.router.classify_intent(prompt)
        self.assertEqual(intent_res["intent"], "DEBUGGING")

        selection = self.model_router.select("DEBUGGING", agent_name="DebugAgent", prompt=prompt)
        self.assertEqual(selection.profile.name, "DEBUGGING")
        self.assertEqual(selection.temperature, 0.0)
        if "qwen2.5-coder:latest" in self.installed_models:
            self.assertEqual(selection.selected_model, "qwen2.5-coder:latest")

    def test_e2e_cloud_computing_general_explanation(self):
        prompt = "What is cloud computing?"
        intent_res = self.router.classify_intent(prompt)
        self.assertIn(intent_res["intent"], ["EXPLANATION", "GENERAL_QA"])

        selection = self.model_router.select(intent_res["intent"], agent_name="ExplanationAgent", prompt=prompt)
        self.assertIn(selection.profile.name, ["EXPLANATION", "GENERAL"])

    def test_e2e_sequential_turn_profile_switching(self):
        """Fifth Critical Test: EXPLANATION -> CODING -> EXPLANATION profile switches correctly."""
        t1_prompt = "Explain Formula 1"
        t1_intent = self.router.classify_intent(t1_prompt)["intent"]
        t1_select = self.model_router.select(t1_intent, agent_name="ExplanationAgent")
        self.assertEqual(t1_select.profile.name, "EXPLANATION")

        t2_prompt = "Write merge sort in Python."
        t2_intent = self.router.classify_intent(t2_prompt)["intent"]
        t2_select = self.model_router.select(t2_intent, agent_name="CodingAgent")
        self.assertEqual(t2_select.profile.name, "CODING")

        t3_prompt = "Explain photosynthesis"
        t3_intent = self.router.classify_intent(t3_prompt)["intent"]
        t3_select = self.model_router.select(t3_intent, agent_name="ExplanationAgent")
        self.assertEqual(t3_select.profile.name, "EXPLANATION")

    def test_quality_vs_speed_performance_matrix(self):
        """Step 23: Quality vs Speed Performance Benchmark."""
        prompts = [
            ("Explain Formula 1", "EXPLANATION", "ExplanationAgent"),
            ("Write binary search in Python", "CODING", "CodingAgent"),
            ("Fix this Python code: a = [1, 2]; print(a[10])", "DEBUGGING", "DebugAgent"),
            ("What is cloud computing?", "EXPLANATION", "ExplanationAgent"),
        ]

        print("\n" + "=" * 85)
        print(" AIFORGE DAY 3 MODEL ROUTING & PERFORMANCE BENCHMARK")
        print("=" * 85)
        print(f"{'Prompt':<45} | {'Profile':<12} | {'Selected Model':<22} | {'Time (s)':<8} | {'Contract'}")
        print("-" * 85)

        for prompt, intent, agent_name in prompts:
            start = time.perf_counter()
            sel = self.model_router.select(intent, agent_name=agent_name, prompt=prompt)
            if agent_name == "ExplanationAgent":
                output = self.explanation_agent.process_explanation_request(prompt)["response"]
            elif agent_name == "CodingAgent":
                output = self.coding_agent.process_coding_request(prompt)["response"]
            elif agent_name == "DebugAgent":
                output = self.debug_agent.process_debug_request(prompt)["response"]

            elapsed = time.perf_counter() - start
            contract = validate_response_contract(intent, prompt, output)
            status = "PASS" if contract["valid"] else "FAIL"

            print(f"{prompt[:44]:<45} | {sel.profile.name:<12} | {sel.selected_model:<22} | {elapsed:<8.3f} | {status}")

        print("=" * 85 + "\n")


if __name__ == "__main__":
    unittest.main()
