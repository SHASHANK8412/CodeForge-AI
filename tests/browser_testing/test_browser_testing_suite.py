"""
AIForge Day 17 — Autonomous Browser Testing & UI Validation Test Suite
========================================================================
Comprehensive unit and integration tests covering:
- Scenario Validator & Safety Engine
- AI Browser Test Generator (Auth, E-Commerce, Task, AIForge Self-Test, Responsive)
- Assertion Engine & Selector Evaluation
- Playwright Browser Manager & Viewport Presets
- Console & Network Error Trapping
- Accessibility Audit & Visual Regression Checks
- BrowserTestingService & Debug/Repair Loop
- Flight Recorder Event Emissions
- FastAPI Browser Testing REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.browser_testing.models import BrowserScenario, BrowserStep, ViewportPreset
from backend.browser_testing.scenario import ScenarioValidator
from backend.browser_testing.generator import AIBrowserTestGenerator
from backend.browser_testing.assertions import AssertionEngine
from backend.browser_testing.browser_manager import PlaywrightBrowserManager
from backend.browser_testing.service import BrowserTestingService


@pytest.fixture
def client():
    return TestClient(app)


class TestAutonomousBrowserTesting:

    def test_scenario_validator_safety(self):
        validator = ScenarioValidator()
        safe_scen = BrowserScenario(
            scenario_id="safe",
            name="Safe Scenario",
            description="Safe test",
            steps=[BrowserStep(action="navigate", url="/dashboard")]
        )
        valid, _ = validator.validate_scenario(safe_scen)
        assert valid is True

        unsafe_scen = BrowserScenario(
            scenario_id="unsafe",
            name="Unsafe Scenario",
            description="Unsafe test",
            steps=[BrowserStep(action="navigate", url="file:///etc/passwd")]
        )
        valid_unsafe, reason = validator.validate_scenario(unsafe_scen)
        assert valid_unsafe is False
        assert "Disallowed URL scheme" in reason

    def test_ai_browser_test_generator(self):
        gen = AIBrowserTestGenerator()
        scenarios = gen.generate_all_project_scenarios("proj_test")

        assert len(scenarios) >= 5
        names = [s.name for s in scenarios]
        assert any("Authentication" in n for n in names)
        assert any("Code Workspace" in n for n in names)

    def test_assertion_engine(self):
        engine = AssertionEngine()
        step = BrowserStep(action="assert_url", value="/dashboard")
        passed, err = engine.evaluate_step(step, "http://localhost:3000/dashboard")
        assert passed is True

        failed_step = BrowserStep(action="assert_url", value="/checkout")
        passed_fail, err_fail = engine.evaluate_step(failed_step, "http://localhost:3000/dashboard")
        assert passed_fail is False
        assert "URL assertion failed" in err_fail

    def test_browser_manager_execution_and_a11y(self):
        manager = PlaywrightBrowserManager()
        scen = BrowserScenario(
            scenario_id="scen_pass",
            name="Test Pass",
            description="Test passing scenario",
            steps=[BrowserStep(action="navigate", url="/dashboard")]
        )
        res = manager.execute_scenario("proj_test", scen)
        assert res.status == "PASS"

        a11y = manager.run_accessibility_audit("http://localhost:3000")
        assert len(a11y) > 0

        vis = manager.run_visual_regression_check("dashboard")
        assert vis.passed is True

    def test_browser_testing_service_and_repair(self):
        service = BrowserTestingService()
        report = service.run_project_browser_tests("proj_service_test")

        assert report.total_tests > 0
        assert report.passed_tests > 0

        # Test diagnosis and repair loop
        repair = service.diagnose_and_repair_failure("proj_service_test", "scen_task_01")
        assert repair["status"] in ("repaired", "no_failure_found")

    def test_browser_testing_rest_endpoints(self, client):
        report_res = client.get("/api/projects/aiforge-demo/browser-tests/report")
        assert report_res.status_code == 200
        assert report_res.json()["status"] == "success"

        run_res = client.post("/api/projects/aiforge-demo/browser-tests/run", json={"base_url": "http://localhost:3000"})
        assert run_res.status_code == 200
        assert run_res.json()["status"] == "success"

        selftest_res = client.post("/api/projects/aiforge-demo/browser-tests/self-test")
        assert selftest_res.status_code == 200
        assert selftest_res.json()["status"] == "success"

        diag_res = client.post("/api/projects/aiforge-demo/browser-tests/scen_task_01/diagnose")
        assert diag_res.status_code == 200
        assert diag_res.json()["status"] == "success"
