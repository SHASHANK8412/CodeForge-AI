"""
tests/test_day14_self_healing.py
==================================
Comprehensive tests for Day 14 Autonomous Review, Debug & Self-Correction Engine.
"""

import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.quality.gates import (
    QualityGate,
    GateStatus,
    FindingSeverity,
    FindingCategory,
    Finding,
    QualityReport,
    evaluate_quality_gates
)
from backend.execution.failure_classifier import classify_test_failure, FailureCategory
from backend.agents.reviewer_agent import global_reviewer_agent
from backend.agents.debug_agent import global_debug_agent
from backend.agents.repair_agent import global_repair_agent, PatchOperation
from backend.quality.version_manager import VersionManager, global_version_manager
from backend.graph.parallel_workflow import route_after_testing


@pytest.fixture()
def app_client():
    from backend.main import app
    return TestClient(app, raise_server_exceptions=True)


class TestDay14SelfHealingEngine:

    def test_reviewer_output_and_quality_gates(self):
        files_map = {
            "backend/main.py": "api_key = 'AKIA1234567890ABCDEF'\nexec('print(1)')",
            "backend/routes/auth.py": "def login():\n    pass"
        }
        report = global_reviewer_agent.analyze_code_quality(files_map)
        assert report.overall_status == GateStatus.FAIL
        assert report.deployment_allowed is False
        assert len(report.findings) >= 2
        assert any(f.severity == FindingSeverity.CRITICAL for f in report.findings)

    def test_finding_schema(self):
        finding = Finding(
            id="finding_123",
            severity=FindingSeverity.HIGH,
            category=FindingCategory.SECURITY,
            file="backend/routes/auth.py",
            line=42,
            message="Authentication input is not validated",
            suggested_fix="Validate request schema before processing",
            blocking=True
        )
        data = finding.model_dump()
        assert data["id"] == "finding_123"
        assert data["severity"] == "HIGH"
        assert data["category"] == "SECURITY"
        assert data["blocking"] is True

    def test_failure_classification(self):
        err_msg = "ModuleNotFoundError: No module named 'fastapi'"
        cf = classify_test_failure(err_msg, test_name="test_startup")
        assert cf.category == FailureCategory.IMPORT_ERROR

        db_err = "sqlite3.OperationalError: no such table: users"
        cf_db = classify_test_failure(db_err, test_name="test_user_create")
        assert cf_db.category == FailureCategory.DATABASE_ERROR

    def test_debug_agent_diagnosis(self):
        state = {
            "project_name": "test_app",
            "execution_results": {"exit_code": 1, "stderr": "ModuleNotFoundError: No module named 'sqlalchemy'"},
            "test_results": {"success": False, "failures": [{"test_name": "test_db", "error": "No module named 'sqlalchemy'"}]},
            "files": {"backend/main.py": "import sqlalchemy"}
        }
        debug_res = global_debug_agent.diagnose_and_repair(state)
        assert debug_res.success is True
        assert debug_res.error_type == "IMPORT_ERROR"
        assert "sqlalchemy" in debug_res.diagnosis

    def test_repair_agent_patch_generation_and_validation(self, tmp_path):
        files_map = {"backend/main.py": "# initial code\ndef run(): pass"}
        plan = global_repair_agent.generate_repair_plan(
            root_cause="Missing import os",
            affected_files=["backend/main.py"],
            classified_failures=[{"message": "No module named 'os'"}],
            files_map=files_map
        )
        assert len(plan.patches) == 1
        patch = plan.patches[0]

        valid = global_repair_agent.validate_and_apply_patch(patch, files_map, project_dir=tmp_path)
        assert valid is True
        assert "import os" in files_map["backend/main.py"]

    def test_snapshot_creation_and_rollback(self, tmp_path):
        vm = VersionManager()
        files = {"main.py": "print('v1')"}
        v1 = vm.create_snapshot("proj_001", files, repair_reason="v1 baseline", test_result={"passed": 5})

        files["main.py"] = "print('v2 broken')"
        v2 = vm.create_snapshot("proj_001", files, repair_reason="v2 broken patch", test_result={"passed": 2})

        assert vm.detect_regression(v1.test_result, v2.test_result, 100.0, 50.0) is True

        rolled_back = vm.rollback("proj_001", files, target_version_id="v1")
        assert rolled_back.version_id == "v1"
        assert files["main.py"] == "print('v1')"

    def test_repair_limit_and_repeated_failure(self):
        vm = VersionManager()
        root_causes = ["Missing database table 'users'", "Missing database table 'users'"]
        assert vm.detect_repeated_failure(root_causes) is True

        state = {
            "execution_results": {"exit_code": 1},
            "test_results": {"success": False},
            "repair_attempt": 3,
            "max_repair_attempts": 3,
            "root_causes": root_causes
        }
        next_route = route_after_testing(state)
        assert next_route == "__end__"
        assert state["status"] in ("FAILED_REPEATED_ROOT_CAUSE", "FAILED_MAX_ITERATIONS")

    def test_quality_and_deployment_gate_blocking(self):
        findings = [
            Finding(id="f1", severity=FindingSeverity.CRITICAL, category=FindingCategory.SECURITY, message="Exposed API key", blocking=True)
        ]
        report = evaluate_quality_gates(findings)
        assert report.deployment_allowed is False

    def test_repair_history_api(self, app_client):
        res = app_client.get("/api/projects/proj_demo/repairs")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert "repairs" in body

    def test_intentionally_broken_project_repair(self, tmp_path):
        files_map = {"backend/main.py": "def test_fn():\n    return 'WRONG'"}
        state = {
            "project_name": "broken_proj",
            "project_path": str(tmp_path),
            "execution_results": {"exit_code": 1, "stderr": "AssertionError: expected 'OK' got 'WRONG'"},
            "test_results": {"success": False, "failures": [{"test_name": "test_fn", "error": "AssertionError"}]},
            "files": files_map,
            "iteration": 0,
            "max_iterations": 3
        }

        debug_res = global_debug_agent.diagnose_and_repair(state)
        assert debug_res.success is True
        assert len(debug_res.files_to_modify) > 0

    def test_failed_repair_stops_safely(self):
        state = {
            "status": "FAILED_MAX_ITERATIONS",
            "execution_results": {"exit_code": 1},
            "test_results": {"success": False},
            "repair_attempt": 3,
            "max_repair_attempts": 3
        }
        route = route_after_testing(state)
        assert route == "__end__"
