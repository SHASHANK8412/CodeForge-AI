"""
AIForge Autonomous Engineering Platform — Comprehensive Test Suite
===================================================================
Test Suite for Autonomous Debug -> Fix -> Retest Loop:
1. Structured Failure Capture (stdout, stderr, exit code, failed tests, stack traces)
2. 12-Category Standard Error Classification
3. Debug Agent 6-Question Diagnosis & Targeted Fix Generation
4. Path Traversal Security Rejection
5. LangGraph Self-Correction Cycle Progression & Checkpointing
6. Max Retries Bound Enforcement (MAX_DEBUG_RETRIES = 3)
7. Repeated Failure Detection & Human Escalation
8. Full End-to-End Simulation: FAIL -> DEBUG -> FIX -> RETEST -> PASS
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any

from backend.graph.project_state import ProjectState
from backend.execution.error_classifier import global_error_classifier, STANDARD_CATEGORIES
from backend.execution.models import DebugResult
from backend.agents.debug_agent import global_debug_agent
from backend.services.project_tester import global_project_tester
from backend.quality.version_manager import global_version_manager
from backend.graph.parallel_workflow import (
    testing_node,
    debug_node,
    patch_node,
    route_after_testing,
    route_after_final_approval,
    final_approval_node,
)


# ===========================================================================
# 1. Error Classification Tests
# ===========================================================================

def test_standard_error_classification_categories():
    """Verify all standard error categories are classified deterministically."""
    cases = [
        ("ModuleNotFoundError: No module named 'jwt'", "IMPORT_ERROR"),
        ("ImportError: cannot import name 'FastAPI'", "IMPORT_ERROR"),
        ("SyntaxError: invalid syntax in file main.py line 42", "SYNTAX_ERROR"),
        ("TypeError: 'NoneType' object is not subscriptable", "TYPE_ERROR"),
        ("AssertionError: assert 404 == 200 in test_api.py", "TEST_ASSERTION_ERROR"),
        ("FAILED tests/test_auth.py::test_login - assert False", "TEST_ASSERTION_ERROR"),
        ("npm ERR! code ERESOLVE could not resolve dependency", "DEPENDENCY_ERROR"),
        ("psycopg2.OperationalError: could not connect to server", "DATABASE_ERROR"),
        ("vite: error when starting dev server - RollupError", "FRONTEND_BUILD_ERROR"),
        ("Application startup failed: Lifespan error", "BACKEND_ERROR"),
        ("FileNotFoundError: [Errno 2] No such file or directory: 'config.json'", "CONFIGURATION_ERROR"),
        ("ZeroDivisionError: division by zero", "RUNTIME_ERROR"),
    ]

    for log_sample, expected_cat in cases:
        classified = global_error_classifier.classify(log_sample)
        assert classified == expected_cat, f"Expected {expected_cat} for '{log_sample}', got {classified}"

    # Detailed classification
    detailed = global_error_classifier.classify_detailed("ModuleNotFoundError: No module named 'foo'")
    assert detailed["category"] == "IMPORT_ERROR"
    assert detailed["severity"] in ("CRITICAL", "HIGH", "MEDIUM")
    assert "import" in detailed["description"].lower()


# ===========================================================================
# 2. Structured Failure Extraction in ProjectTester
# ===========================================================================

def test_project_tester_structured_failure_extraction():
    """Verify ProjectTester extracts command, exit code, failed tests, and stack traces."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "tests" / "test_sample.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("def test_fail():\n    assert 1 == 2\n", encoding="utf-8")

        res = global_project_tester.run_tests(str(tmp_path))

        assert res["overall_status"] in ("PASS", "FAIL")
        assert "command_executed" in res
        assert "exit_code" in res
        assert "duration" in res
        assert "failure_category" in res
        assert isinstance(res["failed_tests"], list)
        assert isinstance(res["stack_traces"], list)


# ===========================================================================
# 3. Debug Agent 6-Question Diagnosis & Targeted Fix
# ===========================================================================

def test_debug_agent_six_question_diagnosis():
    """Verify DebugAgent produces structured diagnosis answering 6 core questions."""
    dummy_state = {
        "files": {
            "backend/main.py": "def get_status():\n    return {'status': 'WRONG'}\n",
            "backend/tests/test_main.py": "from backend.main import get_status\ndef test_status():\n    assert get_status()['status'] == 'OK'\n",
        },
        "test_results": {
            "overall_status": "FAIL",
            "success": False,
            "failed_tests": ["test_status"],
            "failures": ["AssertionError: assert 'WRONG' == 'OK'"],
            "failure_category": "TEST_ASSERTION_ERROR",
            "output": "FAILED backend/tests/test_main.py::test_status - AssertionError: assert 'WRONG' == 'OK'",
        },
        "execution_results": {
            "exit_code": 1,
            "stderr": "AssertionError: assert 'WRONG' == 'OK'",
        },
        "fixes": [],
        "project_name": "TestProject",
    }

    debug_res = global_debug_agent.diagnose_and_repair(dummy_state)

    assert isinstance(debug_res, DebugResult)
    assert debug_res.error_type in ("TEST_ASSERTION_ERROR", "ASSERTION_FAILURE")
    assert "backend/main.py" in debug_res.files_to_modify

    # Verify 6 questions in explanation
    assert "1. What failed:" in debug_res.explanation
    assert "2. Why did it fail:" in debug_res.explanation
    assert "3. Which file is responsible:" in debug_res.explanation
    assert "4. What exact change is required:" in debug_res.explanation
    assert "5. Could this fix break another component:" in debug_res.explanation
    assert "6. How should it be tested:" in debug_res.explanation

    # Verify targeted replacement
    assert "backend/main.py" in debug_res.changes
    assert "OK" in debug_res.changes["backend/main.py"]


# ===========================================================================
# 4. Path Traversal Security Rejection
# ===========================================================================

def test_path_traversal_rejection():
    """Verify malicious file paths are rejected in DebugAgent and PatchNode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        malicious_state = {
            "files": {
                "../../etc/passwd": "root:x:0:0",
                "backend/main.py": "print('ok')",
            },
            "test_results": {
                "overall_status": "FAIL",
                "failures": ["SyntaxError: line 1 in ../../etc/passwd"],
                "failure_category": "SYNTAX_ERROR",
            },
            "execution_results": {"exit_code": 1, "stderr": 'File "../../etc/passwd", line 1'},
            "project_path": str(tmp_path),
        }

        debug_res = global_debug_agent.diagnose_and_repair(malicious_state, project_path=tmp_path)
        for f in debug_res.files_to_modify:
            assert not f.startswith("..")
            assert not f.startswith("/")
            assert not f.startswith("\\")


# ===========================================================================
# 5. LangGraph Self-Correction Nodes Progression
# ===========================================================================

def test_debug_and_patch_nodes_execution():
    """Verify debug_node and patch_node correctly update state, versions, and cycle metadata."""
    async def _runner():
        state = {
            "files": {
                "backend/app.py": "def run():\n    return 'WRONG'\n",
            },
            "test_results": {
                "overall_status": "FAIL",
                "success": False,
                "failed_tests": ["test_run"],
                "failures": ["AssertionError: assert 'WRONG' == 'OK'"],
                "failure_category": "TEST_ASSERTION_ERROR",
                "output": "AssertionError: assert 'WRONG' == 'OK'",
            },
            "execution_results": {
                "exit_code": 1,
                "stderr": "AssertionError: assert 'WRONG' == 'OK'",
            },
            "current_debug_cycle": 0,
            "retry_count": 0,
            "max_retries": 3,
            "project_name": "TestSelfCorrection",
        }

        # Execute debug_node
        debug_out = await debug_node(state)
        assert debug_out["current_debug_cycle"] == 1
        assert debug_out["retry_count"] == 1
        assert "debug_analysis" in debug_out
        assert "proposed_fix" in debug_out
        assert debug_out["current_step"] == "debug"

        # Merge state and execute patch_node
        state.update(debug_out)
        patch_out = await patch_node(state)
        assert patch_out["current_step"] == "patch"
        assert "backend/app.py" in patch_out["files_modified"]
        assert patch_out["files"]["backend/app.py"] == "def run():\n    return 'OK'\n"
        assert len(patch_out["fix_history"]) == 1
        assert patch_out["fix_history"][0]["cycle"] == 1

    asyncio.run(_runner())


# ===========================================================================
# 6. Routing & Max Retry Enforcement (MAX_DEBUG_RETRIES = 3)
# ===========================================================================

def test_route_after_testing_max_retries_and_pass():
    """Verify route_after_testing routes to debug under limit, and escalates when max retries reached."""
    # Case 1: Tests Pass -> route to final_approval
    pass_state = {
        "execution_results": {"exit_code": 0},
        "test_results": {"success": True, "overall_status": "PASS"},
        "retry_count": 1,
        "max_retries": 3,
    }
    assert route_after_testing(pass_state) == "final_approval"
    assert pass_state.get("human_intervention_required") is False

    # Case 2: Tests Fail and retry_count < 3 -> route to debug
    fail_state = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False, "overall_status": "FAIL"},
        "retry_count": 1,
        "max_retries": 3,
        "root_causes": ["Cause A"],
    }
    assert route_after_testing(fail_state) == "debug"

    # Case 3: Tests Fail and retry_count >= 3 -> route to final_approval with escalation
    exhausted_state = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False, "overall_status": "FAIL"},
        "retry_count": 3,
        "max_retries": 3,
        "root_causes": ["Cause A", "Cause B", "Cause C"],
    }
    next_step = route_after_testing(exhausted_state)
    assert next_step == "final_approval"
    assert exhausted_state["human_intervention_required"] is True
    assert exhausted_state["approval_stage"] == "debug_escalation"
    assert exhausted_state["repair_status"] == "STOPPED_MAX_ATTEMPTS"


# ===========================================================================
# 7. Repeated Failure Detection & Human Escalation
# ===========================================================================

def test_repeated_failure_detection_and_escalation():
    """Verify consecutive repeated failures immediately trigger human escalation."""
    repeated_state = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False, "overall_status": "FAIL"},
        "retry_count": 1,
        "max_retries": 3,
        "root_causes": ["Database connection refused", "Database connection refused"],
    }

    next_step = route_after_testing(repeated_state)
    assert next_step == "final_approval"
    assert repeated_state["human_intervention_required"] is True
    assert repeated_state["approval_stage"] == "debug_escalation"
    assert repeated_state["repair_status"] == "STOPPED_REPEATED_FAILURE"


def test_final_approval_escalation_payload():
    """Verify final_approval_node constructs human escalation request when required."""
    async def _runner():
        escalation_state = {
            "human_intervention_required": True,
            "approval_stage": "debug_escalation",
            "project_name": "PaymentService",
            "failed_tests": ["test_stripe_webhook"],
            "stack_traces": ["AssertionError: 400 != 200"],
            "test_results": {"failure_category": "API_ERROR", "passed": 5, "failed": 1},
            "fix_history": [{"cycle": 1, "root_cause": "Bad webhook signature"}],
        }

        out = await final_approval_node(escalation_state)
        assert out["approval_required"] is True
        assert out["approval_stage"] == "debug_escalation"
        req = out["approval_request"]
        assert req["is_escalation"] is True
        assert "AUTOMATIC FIX FAILED" in req["title"]
        assert req["failure_category"] == "API_ERROR"

    asyncio.run(_runner())


# ===========================================================================
# 8. Human Escalation Response & Retry Reset
# ===========================================================================

def test_route_after_final_approval_escalation_actions():
    """Verify user actions in debug escalation route correctly and reset counters."""
    # User provides guidance or clicks retry -> resets counters and routes to debug
    retry_state = {
        "approval_status": "retry",
        "approval_stage": "debug_escalation",
        "retry_count": 3,
    }
    assert route_after_final_approval(retry_state) == "debug"
    assert retry_state["retry_count"] == 0
    assert retry_state["human_intervention_required"] is False

    # User forces proceed -> routes to packaging
    proceed_state = {
        "approval_status": "proceed",
        "approval_stage": "debug_escalation",
    }
    assert route_after_final_approval(proceed_state) == "packaging"
    assert proceed_state["human_intervention_required"] is False


# ===========================================================================
# 9. Full End-to-End Simulation: FAIL -> DEBUG -> FIX -> RETEST -> PASS
# ===========================================================================

def test_end_to_end_debug_fix_retest_loop():
    """
    Simulates full autonomous lifecycle:
    1. Initial verification tests fail.
    2. Workflow routes to debug_node -> diagnoses root cause.
    3. Workflow routes to patch_node -> applies targeted fix.
    4. Workflow returns to testing_node / retest.
    5. Retest passes -> routes to final_approval (Checkpoint 2).
    """
    async def _runner():
        state = {
            "files": {
                "backend/service.py": "def compute():\n    return 'WRONG'\n",
            },
            "test_results": {
                "overall_status": "FAIL",
                "success": False,
                "passed": 0,
                "failed": 1,
                "total": 1,
                "failed_tests": ["test_compute"],
                "failures": ["AssertionError: assert 'WRONG' == 'OK'"],
                "failure_category": "TEST_ASSERTION_ERROR",
                "output": "FAILED tests/test_service.py::test_compute - AssertionError: assert 'WRONG' == 'OK'",
            },
            "execution_results": {
                "exit_code": 1,
                "stderr": "AssertionError: assert 'WRONG' == 'OK'",
            },
            "current_debug_cycle": 0,
            "retry_count": 0,
            "max_retries": 3,
            "project_name": "E2E_SelfRepair_Project",
        }

        # Step 1: Initial check routes to debug
        step_1 = route_after_testing(state)
        assert step_1 == "debug"

        # Step 2: Debug Node analyzes failure
        debug_output = await debug_node(state)
        state.update(debug_output)
        assert state["current_debug_cycle"] == 1
        assert state["error_category"] in ("TEST_ASSERTION_ERROR", "ASSERTION_FAILURE")

        # Step 3: Patch Node applies targeted fix
        patch_output = await patch_node(state)
        state.update(patch_output)
        assert state["files"]["backend/service.py"] == "def compute():\n    return 'OK'\n"

        # Step 4: Retest Simulation
        state["test_results"] = {
            "overall_status": "PASS",
            "success": True,
            "passed": 1,
            "failed": 0,
            "total": 1,
            "failures": [],
            "output": "1 passed in 0.05s",
        }
        state["execution_results"] = {"exit_code": 0, "status": "PASS"}

        # Step 5: Route after retesting -> proceeds to final approval
        step_5 = route_after_testing(state)
        assert step_5 == "final_approval"
        assert state.get("human_intervention_required") is False

    asyncio.run(_runner())

