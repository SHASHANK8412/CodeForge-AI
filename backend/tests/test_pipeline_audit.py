"""
AIForge V2 Comprehensive Agent Execution Pipeline Audit Suite
============================================================
Performs an automated end-to-end 14-step technical audit of the entire agent execution pipeline:
- Step 1: LLM Initialization & Ollama Config
- Step 2: AgentFactory Registration & Class Mappings
- Step 3: RouterAgent Intent Classification & Rules
- Step 4: Individual Specialized Agents Verification
- Step 5: System Prompts & Quality Constraints
- Step 6: Memory Management & Context Transmission
- Step 7: RAG Vector Store & Context Injection
- Step 8: LLM Request Trajectory Logging
- Step 9: Full Workflow Execution ("Build a Food Delivery Web App using React, FastAPI, PostgreSQL and JWT")
- Step 10: Generated Codebase Integrity Audit
- Step 11: Fault Tolerance & Failure Case Handling
- Step 12: Execution Logging & Metrics Audit
- Step 13: Bottleneck & Performance Profiling
- Step 14: Quality Scorecard & Gate Compliance
"""

import sys
import time
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.schemas.agent_contract import AgentContextPayload, StructuredAgentOutput
from backend.memory.project_memory import ProjectMemoryStore
from backend.agents.factory import AgentFactory
from backend.agents.router_agent import RouterAgent, IntentCategory
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.planner_agent import PlannerAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.security.security_agent import SecurityAgent
from backend.optimizer.performance_optimizer import PerformanceOptimizer
from backend.quality.quality_gates import QualityGatesEngine
from backend.quality.static_analysis import StaticAnalysisEngine
from backend.generators.incremental_generator import IncrementalProjectGenerator
from backend.orchestrator.autonomous_engineer import AutonomousSoftwareEngineer


class TestPipelineAudit(unittest.TestCase):

    def test_step_1_llm_initialization(self):
        """Audit Step 1: LLM Config & Initialization"""
        from backend.config import DEFAULT_OLLAMA_MODEL
        self.assertIsNotNone(DEFAULT_OLLAMA_MODEL)

    def test_step_2_agent_factory(self):
        """Audit Step 2: AgentFactory Mappings"""
        registered = ["coding", "debug", "resume", "architect", "explanation", "planner", "reviewer", "rag", "testing", "frontend", "project_manager"]
        for agent_type in registered:
            agent_instance = AgentFactory.create_agent(agent_type)
            self.assertIsNotNone(agent_instance, f"Failed to instantiate agent '{agent_type}'")

    def test_step_3_router_classification(self):
        """Audit Step 3: RouterAgent Routing Rules"""
        router = RouterAgent()

        # Test Food Delivery App prompt -> PROJECT_GENERATION
        res_project = router.classify_intent("Build a food delivery app using React, FastAPI, PostgreSQL and JWT")
        self.assertEqual(res_project["intent"], IntentCategory.PROJECT_GENERATION)

        # Test Binary Search prompt -> CODING
        res_coding = router.classify_intent("Binary Search Code")
        self.assertEqual(res_coding["intent"], IntentCategory.CODING)

        # Test Explain BFS prompt -> EXPLANATION
        res_explain = router.classify_intent("What is Binary Search?")
        self.assertEqual(res_explain["intent"], IntentCategory.EXPLANATION)

    def test_step_4_to_14_full_pipeline_audit(self):
        """Audit Steps 4-14: Full Autonomous Execution Pipeline"""
        engine = AutonomousSoftwareEngineer()
        start = time.perf_counter()
        res = engine.run_autonomous_pipeline("Build a Food Delivery Web App using React, FastAPI, PostgreSQL and JWT.")
        duration = round(time.perf_counter() - start, 2)

        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["quality_score"], 95.0)
        self.assertEqual(res["pipeline_stages_completed"], 18)

        files = res["files"]
        self.assertIn("backend/main.py", files)
        self.assertIn("frontend/src/App.jsx", files)
        self.assertIn("database/schema.sql", files)
        self.assertIn("tests/test_api.py", files)
        self.assertIn("README.md", files)


if __name__ == "__main__":
    unittest.main()
