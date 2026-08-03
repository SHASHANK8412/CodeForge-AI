"""
AIForge Day 2 Prompt Isolation, Response Contracts & Quality Test Suite
======================================================================
Tests:
1. Agent Prompt Isolation (System prompt boundaries for Base, Explanation, Coding, Debug, Resume, RAG).
2. End-to-End Quality Tests (10 Mandatory prompts from Step 18).
3. Cross-Turn Memory Contamination Prevention (Step 19).
4. Same-Word Different-Intent Disambiguation (Step 20).
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.agents.base_agent import BaseAgent
from backend.agents.router_agent import RouterAgent, Intent
from backend.agents.explanation_agent import ExplanationAgent, UNIVERSAL_SYSTEM_PROMPT
from backend.agents.coding_agent import CodingAgent, SYSTEM_PROMPT as CODING_SYSTEM_PROMPT
from backend.agents.debug_agent import DebugAgent, SYSTEM_PROMPT as DEBUG_SYSTEM_PROMPT
from backend.agents.resume_agent import ResumeAgent, SYSTEM_PROMPT as RESUME_SYSTEM_PROMPT
from backend.rag.rag_pipeline import RAGPipeline
from backend.utils.response_contract import validate_response_contract


class TestAgentPromptIsolation(unittest.TestCase):
    """Step 17: Verifies prompt boundaries and isolation across all agents."""

    def test_base_agent_no_forced_headings(self):
        base = BaseAgent("System Prompt", task_name="general")
        prompt = base.build_prompt("Explain Formula 1")
        self.assertNotIn("Response Format", prompt)
        self.assertNotIn("Problem Approach", prompt)
        self.assertNotIn("def solve", prompt)

    def test_explanation_agent_system_prompt_boundaries(self):
        self.assertNotIn("def solve()", UNIVERSAL_SYSTEM_PROMPT)
        self.assertNotIn("Problem Approach", UNIVERSAL_SYSTEM_PROMPT)
        self.assertNotIn("Algorithmic Approach", UNIVERSAL_SYSTEM_PROMPT)
        self.assertIn("Do NOT generate source code unless explicitly requested", UNIVERSAL_SYSTEM_PROMPT)

    def test_coding_agent_system_prompt_boundaries(self):
        self.assertIn("Coding Agent", CODING_SYSTEM_PROMPT)
        self.assertIn("UI components, scripts, or REST endpoints", CODING_SYSTEM_PROMPT)

    def test_debug_agent_system_prompt_boundaries(self):
        self.assertIn("Debugging Agent", DEBUG_SYSTEM_PROMPT)
        self.assertIn("Never invent error tracebacks", DEBUG_SYSTEM_PROMPT)

    def test_resume_agent_system_prompt_boundaries(self):
        self.assertIn("Resume & ATS Specialist Agent", RESUME_SYSTEM_PROMPT)
        self.assertNotIn("def solve", RESUME_SYSTEM_PROMPT)

    def test_rag_pipeline_context_data_separation(self):
        rag = RAGPipeline()
        p = rag.build_prompt("What are transformers?", [])
        self.assertIn("RETRIEVED DOCUMENT CONTEXT (DATA ONLY)", p)
        self.assertIn("USER QUESTION", p)


class TestEndToEndQualityPrompts(unittest.TestCase):
    """Step 18: End-to-end Quality Tests for 10 mandatory prompts."""

    def setUp(self):
        self.router = RouterAgent()
        self.explanation_agent = ExplanationAgent()
        self.coding_agent = CodingAgent()
        self.debug_agent = DebugAgent()
        self.resume_agent = ResumeAgent()
        self.rag_pipeline = RAGPipeline()

    def test_prompt_1_explain_formula_1(self):
        res = self.router.classify_intent("Explain Formula 1")
        self.assertEqual(res["intent"], Intent.EXPLANATION.value)
        self.assertEqual(res["target_agent"], "ExplanationAgent")

        output = self.explanation_agent.process_explanation_request("Explain Formula 1")["response"]
        self.assertIn("Formula 1", output)
        self.assertNotIn("def solve", output)
        self.assertNotIn("Problem Approach", output)
        self.assertNotIn("Algorithmic Approach", output)

        contract = validate_response_contract("EXPLANATION", "Explain Formula 1", output)
        self.assertTrue(contract["valid"])

    def test_prompt_2_explain_photosynthesis_for_child(self):
        res = self.router.classify_intent("Explain photosynthesis to a 10-year-old.")
        self.assertEqual(res["intent"], Intent.EXPLANATION.value)
        output = self.explanation_agent.process_explanation_request("Explain photosynthesis to a 10-year-old.")["response"]
        self.assertIn("Photosynthesis", output)
        self.assertNotIn("```python", output)

    def test_prompt_3_explain_binary_search(self):
        res = self.router.classify_intent("Explain binary search.")
        self.assertEqual(res["intent"], Intent.EXPLANATION.value)
        output = self.explanation_agent.process_explanation_request("Explain binary search.")["response"]
        self.assertIn("Binary Search", output)

    def test_prompt_4_write_binary_search_python(self):
        res = self.router.classify_intent("Write binary search in Python.")
        self.assertEqual(res["intent"], Intent.CODING.value)
        output = self.coding_agent.process_coding_request("Write binary search in Python.")["response"]
        self.assertIn("def binary_search", output)

    def test_prompt_5_create_react_navbar(self):
        res = self.router.classify_intent("Create a React navbar.")
        self.assertEqual(res["intent"], Intent.CODING.value)
        output = self.coding_agent.process_coding_request("Create a React navbar.")["response"]
        self.assertIn("Navbar", output)
        self.assertNotIn("Time Complexity", output)

    def test_prompt_6_debug_index_error(self):
        prompt = "Why does this fail? a = [1, 2]; print(a[10])"
        res = self.router.classify_intent(prompt)
        self.assertEqual(res["intent"], Intent.DEBUGGING.value)
        output = self.debug_agent.process_debug_request(prompt)["response"]
        self.assertIn("IndexError", output)

    def test_prompt_7_what_is_formula_1(self):
        res = self.router.classify_intent("What is Formula 1?")
        self.assertIn(res["intent"], [Intent.EXPLANATION.value, Intent.GENERAL_QA.value])
        output = self.explanation_agent.process_explanation_request("What is Formula 1?")["response"]
        self.assertIn("Formula 1", output)
        self.assertNotIn("def solve", output)

    def test_prompt_8_analyze_resume_ats(self):
        res = self.router.classify_intent("Analyze my resume for ATS issues.")
        self.assertEqual(res["intent"], Intent.RESUME.value)
        output = self.resume_agent.run("Analyze my resume for ATS issues.")
        self.assertIn("Resume", output)
        self.assertNotIn("def solve", output)

    def test_prompt_9_summarize_uploaded_document(self):
        res = self.router.classify_intent("Summarize the document I uploaded.")
        self.assertEqual(res["intent"], Intent.RAG_QUERY.value)
        rag_prompt = self.rag_pipeline.build_prompt("Summarize the document I uploaded.", [])
        self.assertIn("RETRIEVED DOCUMENT CONTEXT (DATA ONLY)", rag_prompt)

    def test_prompt_10_build_complete_task_manager(self):
        res = self.router.classify_intent("Build a complete task management application with React, FastAPI and PostgreSQL.")
        self.assertEqual(res["intent"], Intent.PROJECT_GENERATION.value)


class TestCrossTurnMemoryContamination(unittest.TestCase):
    """Step 19: Sequential conversation turn testing to prevent prompt contamination."""

    def test_sequential_turns_no_leakage(self):
        router = RouterAgent()
        base = BaseAgent("Explanation System Prompt", task_name="explanation")

        # Turn 1: Coding request
        t1_prompt = "Write quicksort in Python."
        t1_intent = router.classify_intent(t1_prompt)["intent"]
        self.assertEqual(t1_intent, Intent.CODING.value)
        t1_output = "def quicksort(arr): return arr"

        # Turn 2: Explanation request with Turn 1 in memory
        t2_prompt = "Explain Formula 1"
        t2_intent = router.classify_intent(t2_prompt)["intent"]
        self.assertEqual(t2_intent, Intent.EXPLANATION.value)

        # BaseAgent.build_prompt should sanitize code from memory context for non-coding tasks
        built_prompt = base.build_prompt(t2_prompt, memory_context=f"User: {t1_prompt}\nAssistant: {t1_output}")
        self.assertNotIn("def quicksort", built_prompt)
        self.assertIn("Explain Formula 1", built_prompt)


class TestSameWordDifferentIntent(unittest.TestCase):
    """Step 20: Disambiguating prompts sharing common words but different intents."""

    def setUp(self):
        self.router = RouterAgent()

    def test_same_word_pairs(self):
        pairs = [
            ("Explain debugging", Intent.EXPLANATION),
            ("Debug this Python program", Intent.DEBUGGING),
            ("Explain React components", Intent.EXPLANATION),
            ("Create a React component", Intent.CODING),
            ("Explain ecommerce architecture", Intent.EXPLANATION),
            ("Build a complete ecommerce system", Intent.PROJECT_GENERATION),
            ("Explain resumes and ATS", Intent.EXPLANATION),
            ("Analyze my resume for ATS", Intent.RESUME),
        ]
        for prompt, expected_intent in pairs:
            res = self.router.classify_intent(prompt)
            self.assertEqual(
                res["intent"],
                expected_intent.value,
                f"Prompt '{prompt}' failed. Expected: {expected_intent.value}, Got: {res['intent']}"
            )


if __name__ == "__main__":
    unittest.main()
