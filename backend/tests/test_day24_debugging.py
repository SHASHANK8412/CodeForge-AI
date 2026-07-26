import pytest
from fastapi.testclient import TestClient

from backend.execution.runner import ProjectExecutionEngine
from backend.debugging.error_classifier import ErrorClassifier
from backend.debugging.analyzer import DebugAnalyzer
from backend.debugging.fixer import AutomaticFixer
from backend.debugging.retry import SelfHealingRetryEngine
from backend.main import app

client = TestClient(app)


def test_project_execution_engine():
    """Test 1: ProjectExecutionEngine runtime checks across backend, frontend, tests, docker."""
    engine = ProjectExecutionEngine()

    files = {
        "frontend/src/App.jsx": "import React from 'react'; export default function App() { return <div>App</div>; }",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef r(): pass",
        "tests/test_api.py": "def test_ok(): assert 1 == 1",
        "backend/Dockerfile": "FROM python:3.12-slim"
    }

    res = engine.execute_project(files)
    assert res["is_healthy"] is True
    assert res["backend_status"] == "success"
    assert res["frontend_status"] == "success"
    assert res["test_status"] == "passed"


def test_error_classifier():
    """Test 2: ErrorClassifier categorization, severity, root cause, and suggested fix."""
    classifier = ErrorClassifier()

    diag = classifier.classify_error("ModuleNotFoundError", "No module named 'requests'", "backend/main.py")
    assert diag["category"] == "Import"
    assert diag["severity"] == "HIGH"
    assert "requirements.txt" in diag["suggested_fix"]


def test_debug_analyzer():
    """Test 3: DebugAnalyzer error parsing and diagnostic generation."""
    analyzer = DebugAnalyzer()

    errors = [
        {"file": "frontend/src/App.jsx", "error": "ExportMissing", "stderr": "Missing export"},
        {"file": "backend/main.py", "error": "SyntaxError", "stderr": "invalid syntax"}
    ]

    res = analyzer.analyze_errors(errors)
    assert res["diagnostics_count"] == 2
    assert res["diagnostics"][0]["category"] == "Frontend"


def test_automatic_fixer():
    """Test 4: AutomaticFixer patch application for missing exports & dependencies."""
    fixer = AutomaticFixer()

    files = {
        "frontend/src/App.jsx": "import React from 'react'; function App() {}",
        "backend/requirements.txt": "fastapi\n"
    }

    diagnostics = [
        {"filepath": "frontend/src/App.jsx", "category": "Frontend"},
        {"filepath": "backend/main.py", "category": "Import"}
    ]

    res = fixer.apply_fixes(files, diagnostics)
    assert res["fixes_applied_count"] >= 1
    assert "export default" in res["patched_files"]["frontend/src/App.jsx"]


def test_self_healing_retry_engine():
    """Test 5: SelfHealingRetryEngine multi-attempt self-healing retry loop."""
    retry_engine = SelfHealingRetryEngine()

    broken_files = {
        "frontend/src/App.jsx": "import React from 'react'; function App() {}", # missing export
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "backend/requirements.txt": "fastapi\n",
        "tests/test_main.py": "def test_ok(): assert True"
    }

    res = retry_engine.execute_self_healing_loop(broken_files, max_attempts=3)
    assert res["status"] == "healthy"
    assert res["self_healing_score"] > 0
    assert "export default" in res["final_files"]["frontend/src/App.jsx"]


def test_debugging_api_endpoints():
    """Test 6: FastAPI Debugging endpoints (/api/execute, /api/debug, /api/execution/logs)."""
    # 1. POST /api/execute/{project_id}
    res_exec = client.post("/api/execute/dbg_test_01")
    assert res_exec.status_code == 200
    assert "is_healthy" in res_exec.json()

    # 2. POST /api/debug/{project_id}
    res_debug = client.post("/api/debug/dbg_test_01")
    assert res_debug.status_code == 200
    assert res_debug.json()["status"] == "healthy"

    # 3. GET /api/execution/logs/{project_id}
    res_logs = client.get("/api/execution/logs/dbg_test_01")
    assert res_logs.status_code == 200
    assert "logs" in res_logs.json()
