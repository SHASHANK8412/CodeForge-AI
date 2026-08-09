"""
Unit Tests & Accuracy Benchmark for AIForge RouterAgent
======================================================
Tests 50+ intent classification prompts across all 8 canonical intents:
- EXPLANATION
- GENERAL_QA
- CODING
- DEBUGGING
- PROJECT_GENERATION
- RESUME
- RAG_QUERY
- UNKNOWN

Enforces Quality Gate >= 90% routing accuracy.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.router_agent import RouterAgent, Intent


TEST_PROMPTS = [
    # --- EXPLANATION (12 Prompts) ---
    ("Explain Formula 1", Intent.EXPLANATION),
    ("How does Formula 1 work?", Intent.EXPLANATION),
    ("Explain binary search", Intent.EXPLANATION),
    ("What is a segmentation fault?", Intent.EXPLANATION),
    ("Explain why Python uses indentation", Intent.EXPLANATION),
    ("What is React?", Intent.EXPLANATION),
    ("Explain Python exceptions", Intent.EXPLANATION),
    ("What is debugging?", Intent.EXPLANATION),
    ("Write an explanation of merge sort", Intent.EXPLANATION),
    ("Explain how Instagram works", Intent.EXPLANATION),
    ("How does DNS work?", Intent.EXPLANATION),
    ("What is polymorphism?", Intent.EXPLANATION),

    # --- GENERAL_QA (5 Prompts) ---
    ("Who invented the telephone?", Intent.GENERAL_QA),
    ("What is the capital of France?", Intent.GENERAL_QA),
    ("When was Python created?", Intent.GENERAL_QA),
    ("Who wrote Hamlet?", Intent.GENERAL_QA),
    ("Where is Mount Everest?", Intent.GENERAL_QA),

    # --- CODING (8 Prompts) ---
    ("Implement binary search in Python", Intent.CODING),
    ("Write Python code to reverse a linked list", Intent.CODING),
    ("Create a React component for a navbar", Intent.CODING),
    ("Write merge sort in Java", Intent.CODING),
    ("Write binary search in Python", Intent.CODING),
    ("Solve Two Sum in Java", Intent.CODING),
    ("Create a REST API in FastAPI", Intent.CODING),
    ("Write Python code for binary search", Intent.CODING),

    # --- DEBUGGING (8 Prompts) ---
    ("My C++ program has a segmentation fault. Fix it.", Intent.DEBUGGING),
    ("Why does this React code crash?", Intent.DEBUGGING),
    ("Explain why this code fails", Intent.DEBUGGING),
    ("Why am I getting NullPointerException?", Intent.DEBUGGING),
    ("Fix this Python code", Intent.DEBUGGING),
    ("My React component crashes", Intent.DEBUGGING),
    ("Why is my code throwing IndexError?", Intent.DEBUGGING),
    ("Why does my Python program throw IndexError?", Intent.DEBUGGING),

    # --- PROJECT_GENERATION (6 Prompts) ---
    ("Build a complete React FastAPI ecommerce website", Intent.PROJECT_GENERATION),
    ("Build an Instagram clone", Intent.PROJECT_GENERATION),
    ("Build a complete expense tracker using React and FastAPI", Intent.PROJECT_GENERATION),
    ("Generate a full ecommerce application", Intent.PROJECT_GENERATION),
    ("Create frontend, backend and database for a task manager", Intent.PROJECT_GENERATION),
    ("Build a Food Delivery App with FastAPI and React", Intent.PROJECT_GENERATION),

    # --- RESUME (5 Prompts) ---
    ("Analyze my resume", Intent.RESUME),
    ("Improve my ATS score", Intent.RESUME),
    ("Improve the ATS score of my resume", Intent.RESUME),
    ("Review my LinkedIn profile bullet points", Intent.RESUME),
    ("Optimize my CV for software engineer roles", Intent.RESUME),

    # --- RAG_QUERY (5 Prompts) ---
    ("Summarize the PDF I uploaded", Intent.RAG_QUERY),
    ("What does the uploaded document say about transformers?", Intent.RAG_QUERY),
    ("Ask questions from the uploaded PDF", Intent.RAG_QUERY),
    ("Summarize this uploaded document", Intent.RAG_QUERY),
    ("What are the key points in the uploaded file?", Intent.RAG_QUERY),

    # --- UNKNOWN / Ambiguous (5 Prompts) ---
    ("Python", Intent.UNKNOWN),
    ("React", Intent.UNKNOWN),
    ("database", Intent.UNKNOWN),
    ("help me with Java", Intent.UNKNOWN),
    ("stuff", Intent.UNKNOWN),
]


class TestRouterAgentAccuracy(unittest.TestCase):

    def setUp(self):
        self.router = RouterAgent()

    def test_routing_accuracy_benchmark(self):
        passed = 0
        total = len(TEST_PROMPTS)
        failed_cases = []

        print(f"\n{'='*80}")
        print(f" AIFORGE ROUTER AGENT BENCHMARK — {total} PROMPTS")
        print(f"{'='*80}")

        for prompt, expected_intent in TEST_PROMPTS:
            res = self.router.classify_intent(prompt)
            actual_intent = res["intent"]
            is_match = (actual_intent == expected_intent.value)

            if is_match:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"
                failed_cases.append((prompt, expected_intent.value, actual_intent, res["reason"]))

            print(f"[{status}] Prompt: '{prompt}' | Expected: {expected_intent.value} | Got: {actual_intent}")

        accuracy = (passed / total) * 100.0

        print(f"\n{'-'*80}")
        print(f" BENCHMARK SUMMARY: {passed}/{total} Passed ({accuracy:.2f}% Accuracy)")
        print(f"{'-'*80}")

        if failed_cases:
            print("\n MISCLASSIFIED PROMPTS:")
            for p, exp, got, r in failed_cases:
                print(f" - Prompt: '{p}'")
                print(f"   Expected: {exp} | Actual: {got}")
                print(f"   Reason:   {r}\n")

        # Quality Gate Check: >= 90% accuracy required!
        self.assertGreaterEqual(
            accuracy,
            90.0,
            f"Routing accuracy {accuracy:.2f}% is below required Quality Gate of 90.0%!"
        )

    def test_explain_formula_1_explicit(self):
        """CRITICAL BUG SPECIFIC TEST: 'Explain Formula 1' must route to EXPLANATION, never CODING."""
        res = self.router.classify_intent("Explain Formula 1")
        self.assertEqual(res["intent"], Intent.EXPLANATION.value)
        self.assertEqual(res["target_agent"], "ExplanationAgent")

    def test_unknown_intent_never_coding(self):
        """Verify UNKNOWN intent never defaults to CodingAgent."""
        res = self.router.classify_intent("Python")
        self.assertEqual(res["intent"], Intent.UNKNOWN.value)
        self.assertNotEqual(res["target_agent"], "CodingAgent")


if __name__ == "__main__":
    unittest.main()
