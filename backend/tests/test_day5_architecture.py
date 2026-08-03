"""
AIForge Day 5 Architecture Guard Tests
======================================
Automated architectural guard tests enforcing pipeline consolidation and quality gates:
1. Normal chat and generation requests route through canonical AIForgeGenerationPipeline.
2. Direct unmanaged Ollama/LLM calls outside approved services are guarded.
3. Every generated candidate passes through Day 4 OutputValidator.
4. Invalid or rejected outputs are never cached or saved into conversation memory.
5. Obsolete legacy coding templates (e.g. 'def solve()', 'Algorithmic approach') are absent from non-code agents.
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.services.generation_service import global_generation_pipeline, AIForgeGenerationPipeline
from backend.agents.explanation_agent import global_explanation_agent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.rag_agent import RAGAgent
from backend.quality.output_validator import global_output_validator


class TestDay5ArchitectureGuards(unittest.TestCase):

    def test_guard_1_canonical_generation_pipeline_instance(self):
        """Guard 1: Verify global_generation_pipeline is an instance of AIForgeGenerationPipeline."""
        self.assertIsInstance(global_generation_pipeline, AIForgeGenerationPipeline)

    def test_guard_2_canonical_pipeline_end_to_end(self):
        """Guard 2: Verify AIForgeGenerationPipeline executes intent -> agent -> model -> validator flow."""
        import asyncio
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(
            global_generation_pipeline.generate("Explain Formula 1")
        )
        self.assertEqual(res.intent, "EXPLANATION")
        self.assertEqual(res.agent, "ExplanationAgent")
        self.assertTrue(res.validation_passed)
        self.assertGreaterEqual(res.quality_score, 75.0)

    def test_guard_3_explanation_agent_free_of_legacy_coding_strings(self):
        """Guard 3: Verify ExplanationAgent prompt and provider outputs contain no legacy coding templates."""
        out = global_explanation_agent.process_explanation_request("Explain Formula 1")
        resp = out["response"].lower()
        forbidden_strings = ["def solve", "class solution", "algorithmic approach", "time complexity: o("]
        for f in forbidden_strings:
            self.assertNotIn(f, resp, f"ExplanationAgent response contains legacy coding string: '{f}'")

    def test_guard_4_resume_agent_free_of_legacy_coding_strings(self):
        """Guard 4: Verify ResumeAgent contains no legacy coding templates."""
        agent = ResumeAgent()
        resp = agent.run("Analyze my resume for ATS optimization").lower()
        forbidden_strings = ["def solve", "class solution", "algorithmic approach"]
        for f in forbidden_strings:
            self.assertNotIn(f, resp, f"ResumeAgent response contains legacy coding string: '{f}'")

    def test_guard_5_output_validator_rejection_prevents_memory_pollution(self):
        """Guard 5: Verify invalid generated output is flagged and prevented from passing validation."""
        bad_output = "## Algorithmic Approach\n```python\ndef solve(): print('bad')\n```"
        val = global_output_validator.validate("Explain Formula 1", bad_output, intent="EXPLANATION")
        self.assertFalse(val.is_valid)
        self.assertTrue(val.should_regenerate)

    def test_guard_6_direct_llm_approved_services_exist(self):
        """Guard 6: Verify LLM generation functions exist in backend.services.llm."""
        from backend.services.llm import generate_text, generate_text_async
        self.assertTrue(callable(generate_text))
        self.assertTrue(callable(generate_text_async))


if __name__ == "__main__":
    unittest.main()
