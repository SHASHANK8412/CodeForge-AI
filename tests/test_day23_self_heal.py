import json
# pyrefly: ignore [missing-import]
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.review.architecture_checker import ArchitectureChecker
from backend.review.security_checker import SecurityChecker
from backend.review.performance_checker import PerformanceChecker
from backend.review.test_parser import TestParser
from backend.review.reviewer import Reviewer
from backend.review.debug import DebugAgent
from backend.review.patch_generator import PatchGenerator
from backend.review.patch_applier import PatchApplier
from backend.review.quality_score import QualityScoreCalculator
from backend.review.report_generator import ReportGenerator
from backend.review.self_heal import SelfHealOrchestrator


def test_architecture_checker(tmp_path):
    checker = ArchitectureChecker()

    # Create mock folders
    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend/src").mkdir(parents=True)

    # 1. Circular dependency files
    (tmp_path / "backend/module_a.py").write_text("from backend.module_b import func_b")
    (tmp_path / "backend/module_b.py").write_text("from backend.module_a import func_a")
    
    # 2. Oversized file
    (tmp_path / "backend/oversized.py").write_text("\n" * 510)

    # 3. Unused import file
    (tmp_path / "backend/unused.py").write_text("import os\nprint('hello')\n")

    # 4. Duplicate module names
    (tmp_path / "frontend/src/unused.py").write_text("print('duplicate')")

    findings = checker.check_project(tmp_path)

    issues = [f["issue"] for f in findings]
    
    assert any("Circular dependency" in issue for issue in issues)
    assert any("Oversized file" in issue for issue in issues)
    assert any("Unused import" in issue for issue in issues)
    assert any("Duplicate module" in issue for issue in issues)


def test_security_checker(tmp_path):
    checker = SecurityChecker()

    (tmp_path / "backend").mkdir()
    
    # 1. Hardcoded API key
    (tmp_path / "backend/secrets.py").write_text("API_KEY = 'secret_api_key_value_here'")

    # 2. SQL injection
    (tmp_path / "backend/db.py").write_text("execute(f'SELECT * FROM users WHERE id = {user_id}')")

    # 3. Command injection
    (tmp_path / "backend/cmd.py").write_text("subprocess.run('ls', shell=True)")

    findings = checker.check_project(tmp_path)
    issues = [f["issue"] for f in findings]

    assert any("hardcoded secret" in issue for issue in issues)
    assert any("SQL Injection" in issue for issue in issues)
    assert any("shell=True" in issue for issue in issues)


def test_performance_checker(tmp_path):
    checker = PerformanceChecker()

    (tmp_path / "backend").mkdir()

    # 1. Blocking sleep in async function
    (tmp_path / "backend/async_block.py").write_text("async def func():\n    time.sleep(5)")

    # 2. Nested loop structure
    (tmp_path / "backend/loops.py").write_text("for i in range(10):\n    for j in range(10):\n        print(i, j)")

    findings = checker.check_project(tmp_path)
    issues = [f["issue"] for f in findings]

    assert any("Blocking 'time.sleep'" in issue for issue in issues)
    assert any("Nested loop" in issue for issue in issues)


def test_test_parser():
    parser = TestParser()

    pytest_log = """
============================= test session starts =============================
collected 3 items

tests/test_auth.py::test_login FAILED                                   [ 33%]
tests/test_auth.py::test_signup PASSED                                  [ 66%]

=================================== FAILURES ===================================
__________________________________ test_login __________________________________
def test_login():
>       assert '200' == '401'
E       AssertionError: assert '200' == '401'

tests/test_auth.py:12: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_auth.py::test_login - AssertionError: assert '200' == '401'
========================= 1 failed, 1 passed in 0.12s =========================
"""

    result = parser.parse_pytest_output(pytest_log)

    assert result["passed"] == 1
    assert result["failed"] == 1
    assert len(result["failures_list"]) == 1
    
    fail = result["failures_list"][0]
    assert fail["test"] == "test_login"
    assert fail["file"] == "tests/test_auth.py"
    assert fail["expected"] == "200"
    assert fail["received"] == "401"
    assert "AssertionError" in fail["traceback"]


@pytest.mark.anyio
@patch("backend.review.reviewer.generate_text_async")
async def test_reviewer_file(mock_gen, tmp_path):
    reviewer = Reviewer()
    
    mock_gen.return_value = json.dumps([
        {
            "severity": "warning",
            "file": "backend/app.py",
            "line": 15,
            "issue": "Naming issue",
            "recommendation": "Use lower_case"
        }
    ])

    test_file = tmp_path / "backend_app.py"
    test_file.write_text("def BadName(): pass")

    findings = await reviewer.review_file(tmp_path, "backend_app.py")
    
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert findings[0]["file"] == "backend_app.py"
    assert findings[0]["issue"] == "Naming issue"


@pytest.mark.anyio
@patch("backend.review.debug.generate_text_async")
async def test_debug_agent(mock_gen):
    agent = DebugAgent()
    
    mock_gen.return_value = json.dumps({
        "root_cause": "Typo in route name",
        "explanation": "Route path expects /users but /user was specified.",
        "proposed_fix": "Change path value to /users",
        "confidence_score": 0.95
    })

    result = await agent.debug_failures("traceback log", "pytest log", ["backend/main.py"])
    
    assert result["confidence_score"] == 0.95
    assert "users" in result["proposed_fix"]
    assert "Typo" in result["root_cause"]


@pytest.mark.anyio
@patch("backend.review.patch_generator.generate_text_async")
async def test_patch_generator(mock_gen):
    gen = PatchGenerator()
    
    mock_gen.return_value = json.dumps({
        "file": "backend/main.py",
        "start_line": 10,
        "end_line": 12,
        "replacement": "def test_func():\n    return True"
    })

    patch_obj = await gen.generate_patch("backend/main.py", "def test_func():\n    pass", "Proposed fix info")
    
    assert patch_obj is not None
    assert patch_obj["start_line"] == 10
    assert "test_func" in patch_obj["replacement"]


def test_patch_applier(tmp_path):
    applier = PatchApplier()

    code_file = tmp_path / "app.py"
    code_file.write_text("""# Line 1
def hello():
    x = 1
    y = 2
    return x + y
# Line 6
""")

    # 1. Successful patch application
    patch_success = {
        "file": "app.py",
        "start_line": 3,
        "end_line": 4,
        "replacement": "    x = 10\n    y = 20"
    }

    res = applier.apply_patch(tmp_path, patch_success)
    assert res is True
    
    content = code_file.read_text()
    assert "x = 10" in content
    assert "y = 20" in content

    # 2. Syntax-invalid patch rollback test
    patch_invalid = {
        "file": "app.py",
        "start_line": 3,
        "end_line": 4,
        "replacement": "    x = === invalid python syntax ==="
    }

    res_invalid = applier.apply_patch(tmp_path, patch_invalid)
    assert res_invalid is False
    
    # Verify rollback restored the working copy
    content_restored = code_file.read_text()
    assert "x = 10" in content_restored
    assert "invalid python" not in content_restored


def test_quality_score():
    calc = QualityScoreCalculator()

    findings = [
        {"severity": "critical", "issue": "hardcoded api_key secret detected"},
        {"severity": "warning", "issue": "circular dependency detected"},
        {"severity": "info", "issue": "nested loop structure detected"}
    ]

    test_results = {"passed": 5, "failed": 0, "errors": 0}

    scores = calc.calculate_scores(findings, test_results)
    
    assert scores["overall"] > 0.0
    assert scores["security"] < 10.0 # deducted for critical secret
    assert scores["architecture"] < 10.0 # deducted for warning circular dependency


@pytest.mark.anyio
@patch("backend.review.self_heal.SelfHealOrchestrator.run_tests")
@patch("backend.review.debug.generate_text_async")
@patch("backend.review.patch_generator.generate_text_async")
async def test_self_heal_orchestration(mock_patch, mock_debug, mock_run, tmp_path):
    orchestrator = SelfHealOrchestrator()

    # Pytest fails initially, then passes on retry
    mock_run.side_effect = [
        (1, "\n__________________________________ test_app __________________________________\nAssertionError in tests/test_app.py"),
        (0, "========================= 2 passed in 0.10s =========================")
    ]

    mock_debug.return_value = json.dumps({
        "root_cause": "Assertion failure",
        "explanation": "mismatch",
        "proposed_fix": "Use correct assertions",
        "confidence_score": 0.9
    })

    # Prepare project directory
    (tmp_path / "backend").mkdir()
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests/test_app.py"
    test_file.write_text("def test_app(): assert False")

    mock_patch.return_value = json.dumps({
        "file": "tests/test_app.py",
        "start_line": 1,
        "end_line": 1,
        "replacement": "def test_app(): assert True"
    })

    findings, test_results, scores, report = await orchestrator.execute_self_heal_pipeline("TestApp", tmp_path)

    assert test_results["passed"] == 2
    assert (tmp_path / "reports/project_review.md").exists()
    assert scores["overall"] > 0.0
