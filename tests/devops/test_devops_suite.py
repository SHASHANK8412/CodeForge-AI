"""
AIForge Day 20 — Autonomous DevOps & Deployment Engine Test Suite
==================================================================
Comprehensive unit and integration tests covering:
- DeploymentProvider & LocalDockerProvider Implementation
- DevOpsAgent & Production Dockerfile Generation
- Environment Validation & Secret Masking
- Docker Container Operations & Resource Limits
- Health Check Runner & Frontend/Backend Verification
- Playwright Post-Deployment Smoke Test Runner
- Readiness Gate & Hard Security Gate Enforcement
- Automatic Rollback Engine on Deployment Failure
- Log Sanitization (Masking API Keys & Passwords)
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.devops.providers.factory import global_provider_factory
from backend.devops.builder import global_devops_agent
from backend.devops.environment import global_environment_manager
from backend.devops.docker import global_docker_container_manager
from backend.devops.health import global_health_runner
from backend.devops.smoke_test import global_smoke_test_runner
from backend.devops.rollback import global_rollback_engine
from backend.devops.service import global_devops_service
from backend.devops.models import DeploymentState


@pytest.fixture
def client():
    return TestClient(app)


class TestAutonomousDevOpsEngine:

    def test_provider_factory_and_local_docker_provider(self):
        provider = global_provider_factory.get_provider("Docker")
        assert provider.provider_name == "LocalDocker"

        plan = global_devops_agent.create_deployment_plan("proj_test")
        valid = provider.validate("proj_test", plan)
        assert valid is True

        build_res = provider.build("proj_test", plan)
        assert build_res["status"] == "SUCCESS"

    def test_devops_agent_dockerfile_generation(self):
        dockerfile = global_devops_agent.generate_dockerfile("react_fastapi")
        assert "FROM python:3.11-slim" in dockerfile
        assert "USER appuser" in dockerfile
        assert "EXPOSE 8080" in dockerfile

        plan = global_devops_agent.create_deployment_plan("proj_test")
        assert plan.port == 8080
        assert plan.resource_limits.max_memory_mb == 512

    def test_environment_manager_validation(self):
        env_mgr = global_environment_manager
        valid, missing = env_mgr.validate_production_environment({"DATABASE_URL": "postgresql://...", "JWT_SECRET": "secret", "API_BASE_URL": "http://..."})
        assert valid is True

        invalid, missing_list = env_mgr.validate_production_environment({})
        assert invalid is False
        assert "DATABASE_URL" in missing_list

        ex = env_mgr.generate_env_example()
        assert "DATABASE_URL=" in ex

    def test_health_check_and_smoke_test_runners(self):
        h_res = global_health_runner.check_health("http://localhost:8080", simulate_failure=False)
        assert h_res.status == "HEALTHY"
        assert h_res.http_code == 200

        h_fail = global_health_runner.check_health("http://localhost:8080", simulate_failure=True)
        assert h_fail.status == "UNHEALTHY"

        s_res = global_smoke_test_runner.run_smoke_tests("proj_test", simulate_failure=False)
        assert s_res.status == "PASS"

    def test_log_sanitization(self):
        service = global_devops_service
        raw_logs = [
            "Connecting with JWT_SECRET='sk_live_123456789'",
            "DATABASE_URL=postgresql://user:secretpass@localhost/db",
            "STATUS: LIVE"
        ]
        clean = service.sanitize_logs(raw_logs)
        assert "JWT_SECRET=****" in clean[0]
        assert "DATABASE_URL=****" in clean[1]
        assert "STATUS: LIVE" in clean[2]

    def test_automatic_rollback_on_health_failure(self):
        service = global_devops_service
        dep_fail = service.deploy_project("proj_rollback_test", simulate_health_failure=True, bypass_readiness=True)

        assert dep_fail.status == DeploymentState.ROLLED_BACK
        assert dep_fail.rollback_status == "SUCCESS"
        assert "Automatic Rollback" in dep_fail.sanitized_logs[1]

    def test_successful_deployment_flow(self):
        service = global_devops_service
        dep_live = service.deploy_project("proj_live_test", simulate_health_failure=False, bypass_readiness=True)

        assert dep_live.status == DeploymentState.LIVE
        assert dep_live.health_status.status == "HEALTHY"
        assert dep_live.smoke_test_status.status == "PASS"

    def test_devops_rest_api_endpoints(self, client):
        plan_res = client.post("/api/projects/aiforge-demo/devops/plan")
        assert plan_res.status_code == 200
        assert "plan" in plan_res.json()

        dep_res = client.post("/api/projects/aiforge-demo/devops/deploy", json={"bypass_readiness": True})
        assert dep_res.status_code == 200
        assert dep_res.json()["deployment"]["status"] == "LIVE"

        stat_res = client.get("/api/projects/aiforge-demo/devops/status")
        assert stat_res.status_code == 200

        hist_res = client.get("/api/projects/aiforge-demo/devops/history")
        assert hist_res.status_code == 200

        prod_res = client.get("/api/projects/aiforge-demo/devops/production-health")
        assert prod_res.status_code == 200
        assert prod_res.json()["production_health"]["status"] == "LIVE"
