"""
PyTest Unit & Integration Test Suite: AIForge Autonomous AI Software Engineer Engine
===================================================================================
Verifies:
1. Universal Context Delivery & Structured JSON Agent Contracts
2. Persistent Project Memory Store
3. Security Agent Auto-Fix Engine
4. Performance Optimizer Engine
5. 15-Check Quality Gates Engine (Enforces >= 95/100 score)
6. Full 18-Stage Autonomous Pipeline Execution
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.schemas.agent_contract import AgentContextPayload, StructuredAgentOutput, FileArtifact
from backend.memory.project_memory import ProjectMemoryStore
from backend.security.security_agent import SecurityAgent
from backend.optimizer.performance_optimizer import PerformanceOptimizer
from backend.quality.quality_gates import QualityGatesEngine
from backend.orchestrator.autonomous_engineer import AutonomousSoftwareEngineer


class TestAutonomousEngineerEngine(unittest.TestCase):

    def test_structured_agent_contract(self):
        payload = AgentContextPayload(
            project_goal="Develop E-Commerce Platform",
            task_description="Build Auth Handler",
            expected_output="FastAPI Router"
        )
        self.assertEqual(payload.project_goal, "Develop E-Commerce Platform")

        file_art = FileArtifact(path="app/auth.py", purpose="JWT Auth", content="def login(): pass")
        output = StructuredAgentOutput(
            project_name="E-Commerce",
            task="auth",
            agent_name="AuthAgent",
            files=[file_art],
            quality_score=98.0
        )
        self.assertEqual(output.quality_score, 98.0)
        self.assertEqual(len(output.files), 1)

    def test_project_memory_store(self):
        mem = ProjectMemoryStore("Test Project")
        mem.save_file("backend/main.py", "print('hello')", "Main entry point")
        content = mem.get_file("backend/main.py")
        self.assertEqual(content, "print('hello')")
        all_files = mem.get_all_generated_files()
        self.assertIn("backend/main.py", all_files)

    def test_security_agent_autofix(self):
        sec = SecurityAgent()
        files = {
            "app/config.py": "SECRET_KEY = 'secret'",
            "app/db.py": "query = f'SELECT * FROM users WHERE email={email}'"
        }
        remedied_files, report = sec.scan_and_remedy(files)
        self.assertGreaterEqual(report["security_score"], 95.0)
        self.assertIn("os.getenv", remedied_files["app/config.py"])
        self.assertGreaterEqual(report["vulnerabilities_auto_fixed"], 1)

    def test_performance_optimizer(self):
        opt = PerformanceOptimizer()
        files = {
            "app/router.py": "def get_items(): return []",
            "src/Navbar.jsx": "import React from 'react'; export default function Navbar() { return <div />; }"
        }
        opt_files, report = opt.optimize_codebase(files)
        self.assertGreaterEqual(report["performance_score"], 95.0)
        self.assertIn("async def get_items", opt_files["app/router.py"])

    def test_quality_gates_engine(self):
        qg = QualityGatesEngine()
        files = {
            "frontend/src/App.jsx": "export default function App() { return <div className='flex' />; }",
            "backend/main.py": "from fastapi import FastAPI, APIRouter; from pydantic import BaseModel; import os; app = FastAPI(); router = APIRouter(); auth_secret = os.getenv('JWT_SECRET')",
            "database/schema.sql": "CREATE TABLE users (id UUID PRIMARY KEY);",
            "tests/test_api.py": "def test_pass(): pass",
            "README.md": "# Test Project"
        }
        sec_report = {"security_score": 98.0}
        perf_report = {"performance_score": 98.0}
        res = qg.evaluate_project(files, sec_report, perf_report)
        self.assertTrue(res.passed)
        self.assertGreaterEqual(res.score, 95.0)
        self.assertEqual(len(res.gate_checks), 15)

    def test_full_18_stage_autonomous_pipeline(self):
        engine = AutonomousSoftwareEngineer()
        res = engine.run_autonomous_pipeline("Develop Formula 1 Web Application")
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["quality_score"], 95.0)
        self.assertEqual(res["pipeline_stages_completed"], 18)
        self.assertIn("backend/main.py", res["files"])
        self.assertIn("frontend/src/App.jsx", res["files"])
        self.assertIn("database/schema.sql", res["files"])


if __name__ == "__main__":
    unittest.main()
