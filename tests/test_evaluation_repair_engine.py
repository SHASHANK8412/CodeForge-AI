import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from backend.evaluation.models import (
    EvaluationScoreBreakdown,
    EvaluationTestSummary,
    ProjectEvaluationResult,
    EvaluateProjectRequest
)
from backend.evaluation.scoring import ProjectScoreCalculator
from backend.evaluation.test_runner import EvaluationTestRunner
from backend.evaluation.repair_engine import AutonomousSelfRepairEngine
from backend.evaluation.evaluator import ProjectEvaluator
from backend.execution.models import ExecutionResult, DebugResult


def test_1_successful_project_evaluation(tmp_path):
    # Test 1: Successful project evaluation
    evaluator = ProjectEvaluator()
    proj_dir = tmp_path / "TodoApp"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "README.md").write_text("# Todo Application\nIncludes user authentication and CRUD endpoints.", encoding="utf-8")
    (proj_dir / "main.py").write_text("def create_todo(): pass\ndef auth_user(): pass", encoding="utf-8")


    mock_exec = ExecutionResult(exit_code=0, status="PASS", stdout="19 passed in 0.2s", stderr="")
    with patch("backend.execution.project_runner.global_project_runner.run_project", return_value=mock_exec):
        res: ProjectEvaluationResult = evaluator.evaluate_and_repair_project(
            project_path=str(proj_dir),
            requirements="Build a todo application with authentication",
            max_repair_attempts=3
        )

        assert res.final_status == "PASSED"
        assert res.overall_score >= 80.0
        assert res.test_results.tests_passed == 19
        assert res.test_results.tests_failed == 0
        assert res.repair_attempts == 0


def test_2_failed_test_detection(tmp_path):
    # Test 2: Failed test detection
    runner = EvaluationTestRunner()
    proj_dir = tmp_path / "FailedApp"
    proj_dir.mkdir(parents=True, exist_ok=True)

    mock_exec = ExecutionResult(exit_code=1, status="FAIL", stdout="18 passed, 1 failed in 0.5s", stderr="AssertionError: 401 != 200")
    with patch("backend.execution.project_runner.global_project_runner.run_project", return_value=mock_exec):
        res = runner.run_tests(str(proj_dir))
        summary: EvaluationTestSummary = res["summary"]

        assert summary.success is False
        assert summary.tests_passed == 18
        assert summary.tests_failed == 1
        assert "AssertionError" in res["failure_output"]


def test_3_and_4_debug_agent_invocation_and_successful_repair(tmp_path):
    # Test 3 & 4: DebugAgent invocation and successful repair on second attempt
    engine = AutonomousSelfRepairEngine()
    proj_dir = tmp_path / "RepairApp"
    proj_dir.mkdir(parents=True, exist_ok=True)
    todo_file = proj_dir / "backend" / "todos.py"
    todo_file.parent.mkdir(parents=True, exist_ok=True)
    todo_file.write_text("def get_todos(): return None", encoding="utf-8")

    mock_fail = ExecutionResult(exit_code=1, status="FAIL", stdout="0 passed, 1 failed", stderr="AttributeError: NoneType has no len")
    mock_pass = ExecutionResult(exit_code=0, status="PASS", stdout="1 passed in 0.1s", stderr="")

    exec_side_effects = [mock_fail, mock_pass]
    mock_debug_res = DebugResult(
        error_type="NullReference",
        root_cause="Returned None instead of list",
        diagnosis="Fix return value",
        changes={"backend/todos.py": "def get_todos(): return []"},
        files_to_modify=["backend/todos.py"],
        confidence=0.95
    )

    with patch("backend.execution.project_runner.global_project_runner.run_project", side_effect=exec_side_effects):
        with patch("backend.agents.debug_agent.global_debug_agent.diagnose_and_repair", return_value=mock_debug_res) as mock_debug:
            res = engine.run_repair_loop(
                project_path=str(proj_dir),
                user_prompt="Build a todo application",
                files_map={"backend/todos.py": "def get_todos(): return None"},
                max_repair_attempts=3
            )

            assert mock_debug.called
            assert res["final_status"] == "PASSED"
            assert res["repair_attempts"] == 1
            assert "backend/todos.py" in res["repaired_files"]
            assert todo_file.read_text(encoding="utf-8") == "def get_todos(): return []"


def test_5_6_7_10_multiple_repair_attempts_and_max_limit_no_infinite_loops(tmp_path):
    # Test 5, 6, 7, 10: Multiple repair attempts, max limit reached, final failure status, no infinite loop
    engine = AutonomousSelfRepairEngine()
    proj_dir = tmp_path / "UnrepairableApp"
    proj_dir.mkdir(parents=True, exist_ok=True)

    mock_fail = ExecutionResult(exit_code=1, status="FAIL", stdout="0 passed, 1 failed", stderr="Persistent SyntaxError")
    mock_debug_res = DebugResult(
        error_type="SyntaxError",
        root_cause="Syntax bug",
        diagnosis="Attempt fix",
        changes={"bad.py": "invalid syntax"},
        files_to_modify=["bad.py"],
        confidence=0.5
    )

    with patch("backend.execution.project_runner.global_project_runner.run_project", return_value=mock_fail):
        with patch("backend.agents.debug_agent.global_debug_agent.diagnose_and_repair", return_value=mock_debug_res):
            res = engine.run_repair_loop(
                project_path=str(proj_dir),
                user_prompt="Broken app",
                files_map={},
                max_repair_attempts=3
            )

            assert res["final_status"] == "FAILED"
            assert res["repair_attempts"] == 3
            assert len(res["remaining_errors"]) > 0


def test_8_score_calculation():
    # Test 8: 100-point score calculation
    calc = ProjectScoreCalculator()
    fidelity_result = {"domain_matched": True, "feature_coverage": 96.0}
    test_summary = {"total_tests": 20, "tests_passed": 20, "tests_failed": 0, "success": True}
    security_report = {"score": 90.0}
    architecture_spec = {"routes": ["GET /todos"], "models": ["Todo"]}
    static_analysis_report = {"bugs_count": 0}

    scores: EvaluationScoreBreakdown = calc.calculate_scores(
        fidelity_result=fidelity_result,
        test_summary=test_summary,
        security_report=security_report,
        architecture_spec=architecture_spec,
        static_analysis_report=static_analysis_report,
        has_documentation=True
    )

    assert scores.requirement_coverage == 19.2
    assert scores.code_correctness == 20.0
    assert scores.tests == 20.0
    assert scores.security == 13.5
    assert scores.architecture == 10.0
    assert scores.code_quality == 10.0
    assert scores.documentation == 5.0
    assert scores.overall_score == 97.7


def test_9_api_response_validation():
    # Test 9: API endpoint response validation
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    mock_eval = ProjectEvaluationResult(
        project_name="TodoApp",
        requirements="Build todo app",
        overall_score=94.0,
        final_status="PASSED",
        scores=EvaluationScoreBreakdown(),
        test_results=EvaluationTestSummary(total_tests=20, tests_passed=20, success=True),
        repair_attempts=1,
        repaired_files=["backend/routes/todos.py"],
        remaining_errors=[]
    )

    with patch("backend.evaluation.evaluator.global_project_evaluator.evaluate_and_repair_project", return_value=mock_eval):
        res = client.post("/api/evaluate", json={
            "requirements": "Build a todo application with authentication",
            "max_repair_attempts": 3
        })

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "PASSED"
        assert data["score"] == 94.0
        assert data["repair_attempts"] == 1
        assert "evaluation" in data
        assert "test_results" in data
