import pytest
from backend.agents.requirement_fidelity_agent import RequirementFidelityAgent
from backend.validation.quality_score import QualityScoreCalculator
from backend.exporter.gate import ExportGate


def test_infer_expected_domain():
    agent = RequirementFidelityAgent()
    assert agent.infer_expected_domain("build a todo list app") == "Productivity / Task Management"
    assert agent.infer_expected_domain("create an ecommerce store") == "E-Commerce / Shopping"
    assert agent.infer_expected_domain("build a blog api with comments") == "Blogging / Content Management"
    assert agent.infer_expected_domain("expense tracker using react") == "Finance / Expense Tracking"
    assert agent.infer_expected_domain("formula 1 racing website") == "Sports / Motorsport"


def test_evaluate_fidelity_domain_mismatch():
    agent = RequirementFidelityAgent()
    # Prompt asks for Todo App, but spec and files contain Formula 1 / Motorsport
    prompt = "build a todo list app"
    proj_spec = {"project_name": "Software Project", "domain": "Sports / Motorsport", "requirements": ["Formula 1 racing drivers"]}
    arch_spec = {"domain": "Sports / Motorsport"}
    files = {"backend/main.py": "def get_f1_drivers(): pass"}

    res = agent.evaluate_fidelity(prompt, proj_spec, arch_spec, files)
    assert res["status"] == "FAIL"
    assert res["domain_matched"] is False
    assert res["fidelity_score"] <= 20.0
    assert "Requirement Fidelity FAILED" in res["reason"]


def test_evaluate_fidelity_domain_match():
    agent = RequirementFidelityAgent()
    prompt = "build a todo list app"
    proj_spec = {"project_name": "TodoApp", "domain": "Productivity / Task Management", "requirements": ["Create tasks", "Mark tasks complete"]}
    arch_spec = {"domain": "Productivity / Task Management"}
    files = {"backend/main.py": "def create_task(): pass", "frontend/App.jsx": "function TodoList() { return <div>Tasks</div>; }"}

    res = agent.evaluate_fidelity(prompt, proj_spec, arch_spec, files)
    assert res["status"] == "PASS"
    assert res["domain_matched"] is True
    assert res["fidelity_score"] >= 80.0
    assert "Requirement Match PASS" in res["reason"]


def test_quality_score_calculator_penalizes_fidelity_failure():
    calc = QualityScoreCalculator()
    fid_failed = {
        "expected_domain": "Productivity / Task Management",
        "generated_domain": "Sports / Motorsport",
        "domain_matched": False,
        "fidelity_score": 15.0,
        "status": "FAIL",
        "reason": "Domain mismatch"
    }

    sc = calc.compute_score([], has_docs=True, requirement_fidelity=fid_failed)
    assert sc.grade == "FAIL"
    assert sc.ready_for_export is False


def test_export_gate_denies_on_fidelity_failure():
    gate = ExportGate()
    state = {
        "execution_results": {"exit_code": 0, "status": "PASS"},
        "test_results": {"success": True, "failed": 0},
        "status": "PASS",
        "project_path": "c:/valid/dir",
        "files": {"main.py": "pass"},
        "requirement_fidelity": {
            "status": "FAIL",
            "domain_matched": False,
            "reason": "Generated domain 'Sports / Motorsport' does not match prompt 'build a todo list app'"
        }
    }

    # Mock Path.exists to true
    from unittest.mock import patch, MagicMock
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.is_dir", return_value=True):
            res = gate.validate_state(state)
            assert res.allowed is False
            assert "Requirement Fidelity Failed" in res.reason
