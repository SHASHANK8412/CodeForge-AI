import pytest
from backend.agents.build_validation_agent import BuildValidationAgent
from backend.agents.dependency_manager_agent import DependencyManagerAgent
from backend.agents.project_execution_agent import ProjectExecutionAgent
from backend.agents.file_quality_agent import FileQualityAgent
from backend.agents.security_agent import SecurityAgent
from backend.agents.performance_agent import PerformanceAgent
from backend.agents.project_testing_agent import ProjectTestingAgent
from backend.agents.project_packaging_agent import ProjectPackagingAgent


def test_build_validation_agent():
    agent = BuildValidationAgent()
    fe_files = {"App.jsx": "export default function App() { return <div>Test</div>; }"}
    be_files = {"main.py": "def test():\n    return 'ok'"}
    db_code = "CREATE TABLE users (id INT PRIMARY KEY);"
    dk_files = {"Dockerfile": "FROM python:3.11\nWORKDIR /app"}

    report = agent.validate_all(fe_files, be_files, db_code, dk_files)
    assert report.is_valid is True
    assert report.frontend_valid is True
    assert report.backend_valid is True


def test_dependency_manager_agent():
    agent = DependencyManagerAgent()
    be_files = {"main.py": "import fastapi\nimport uvicorn\nfrom pydantic import BaseModel"}
    fe_files = {"App.jsx": "import React from 'react';\nimport axios from 'axios';"}

    manifests = agent.run_dependency_analysis("TestApp", be_files, fe_files)
    assert "requirements.txt" in manifests
    assert "package.json" in manifests
    assert "fastapi" in manifests["requirements.txt"]
    assert "axios" in manifests["package.json"]


def test_project_execution_agent():
    agent = ProjectExecutionAgent()
    be_files = {"main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {}"}
    fe_files = {"App.jsx": "export default function App() {}"}
    db_code = "postgresql://localhost:5432/db"

    report = agent.verify_execution(be_files, fe_files, db_code)
    assert report.server_starts is True
    assert report.no_crashes is True


def test_file_quality_agent():
    agent = FileQualityAgent()
    files = {
        "good.py": "def add(a, b):\n    return a + b\n",
        "bad.py": "def bad():\n    # TODO fix later\n    pass\n"
    }

    report = agent.audit_project(files)
    assert report.total_files == 2
    assert len(report.violations) >= 1


def test_security_agent():
    agent = SecurityAgent()
    files = {
        "main.py": "SECRET_KEY = 'supersecretkey123'\nquery = f'SELECT * FROM users WHERE id={user_id}'"
    }

    report = agent.scan_files(files)
    assert report.is_secure is False
    assert len(report.vulnerabilities) >= 1


def test_performance_agent():
    agent = PerformanceAgent()
    report = agent.collect_metrics(total_time=1.5, agent_times={"planner": 0.5, "architect": 1.0}, estimated_tokens=5000)
    assert report.total_generation_time_seconds == 1.5
    assert len(report.agent_metrics) == 2


def test_project_testing_agent():
    agent = ProjectTestingAgent()
    suites = agent.generate_all_tests("TestApp", "backend_code", "frontend_code")
    report = agent.build_report(suites)
    assert report.is_passed is True
    assert report.total_tests > 0


def test_project_packaging_agent():
    agent = ProjectPackagingAgent()
    zip_bytes = agent.create_zip_bytes({"README.md": "# Test Project"})
    assert len(zip_bytes) > 0
