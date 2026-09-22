"""
Test Suite: Autonomous DevOps & One-Click Deployment
===================================================
Tests project analysis, readiness scoring, secret scanner gates,
environment masking, Docker / CI/CD generation, explicit approval
enforcement, health check verification, DevOps copilot diagnostics,
and rollback memory persistence.
"""

import pytest
from pathlib import Path
from starlette.testclient import TestClient

from backend.main import app
from backend.agents.devops_agent import global_devops_agent, DevOpsAgent
from backend.deployment.secret_scanner import global_secret_scanner
from backend.deployment.environment_manager import global_environment_manager
from backend.deployment.devops_copilot import global_devops_copilot
from backend.deployment.rollback_manager import global_rollback_manager
from backend.memory.project_memory_service import global_project_memory_service


@pytest.fixture
def sample_devops_files():
    return {
        "backend/main.py": """
from fastapi import FastAPI
import os

app = FastAPI()
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/db")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/products")
def get_products():
    return [{"id": 1, "title": "Keyboard"}]
""",
        "frontend/src/App.jsx": """
import React from 'react';
export default function App() {
    return <h1>AIForge Store</h1>;
}
""",
        "package.json": '{"name": "frontend", "scripts": {"build": "vite build"}}',
        "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\npsycopg2-binary\n",
        "database/schema.sql": "CREATE TABLE products (id SERIAL PRIMARY KEY, title VARCHAR(255));\n"
    }


def test_devops_project_analysis_and_spec_detection(sample_devops_files):
    agent = DevOpsAgent()
    spec = agent.analyze_project("ecommerce_test", sample_devops_files)

    assert spec.frontend_tech.lower() in ("react", "vite")
    assert spec.backend_tech.lower() == "fastapi"
    assert spec.database_tech == "postgresql"
    assert "DATABASE_URL" in spec.required_env_vars or "JWT_SECRET" in spec.required_env_vars
    assert spec.health_check_endpoint == "/health"


def test_deployment_readiness_score_calculation(sample_devops_files):
    agent = DevOpsAgent()
    readiness = agent.evaluate_readiness("ecommerce_test", sample_devops_files, test_pass_rate=1.0)

    assert readiness.score >= 80.0
    assert readiness.is_ready is True
    assert readiness.status in ("READY", "WARNING")
    assert len(readiness.blockers) == 0

    # Test failing test rate generates blockers
    bad_readiness = agent.evaluate_readiness("ecommerce_test", sample_devops_files, test_pass_rate=0.5)
    assert bad_readiness.is_ready is False
    assert bad_readiness.status == "BLOCKED"
    assert len(bad_readiness.blockers) > 0


def test_secret_scanner_blocks_deployment_on_leaks():
    leaked_files = {
        "backend/config.py": """
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE123"
API_KEY = "sk-live-99887766554433221100"
"""
    }
    scan_res = global_secret_scanner.scan_files(leaked_files)
    assert scan_res.is_clean is False
    assert scan_res.total_findings >= 1

    # Ensure findings are masked
    for finding in scan_res.findings:
        assert "••••" in finding.masked_value

    agent = DevOpsAgent()
    readiness = agent.evaluate_readiness("leak_test", leaked_files, secrets_result=scan_res)
    assert readiness.is_ready is False
    assert readiness.status == "BLOCKED"


def test_environment_manager_masks_secrets():
    mgr = global_environment_manager
    mgr.configure_environment("test_env_proj", {
        "DATABASE_URL": "postgresql://usr:secret_pass@db.neon.tech/appdb",
        "JWT_SECRET": "my_super_secret_jwt_signing_key_long_string"
    })

    res = mgr.validate_environment("test_env_proj", ["DATABASE_URL", "JWT_SECRET"])
    assert res.is_valid is True
    assert "DATABASE_URL" in res.variables
    assert "••••" in res.variables["DATABASE_URL"].masked_value
    assert "secret_pass" not in res.variables["DATABASE_URL"].masked_value


def test_docker_and_compose_generation(sample_devops_files):
    agent = DevOpsAgent()
    spec = agent.analyze_project("ecommerce_test", sample_devops_files)
    configs = agent.generate_docker_configuration(spec)

    assert "Dockerfile" in configs
    assert ".dockerignore" in configs
    assert "docker-compose.yml" in configs
    assert "uvicorn" in configs["Dockerfile"]
    assert "postgres" in configs["docker-compose.yml"]


def test_cicd_github_actions_generation(sample_devops_files):
    agent = DevOpsAgent()
    spec = agent.analyze_project("ecommerce_test", sample_devops_files)
    cicd = agent.generate_cicd_pipeline(spec)

    assert ".github/workflows/ci.yml" in cicd
    assert "pytest" in cicd[".github/workflows/ci.yml"]
    assert "docker build" in cicd[".github/workflows/ci.yml"]


def test_explicit_user_approval_enforcement(sample_devops_files):
    import asyncio
    agent = DevOpsAgent()
    plan = agent.prepare_deployment_plan("approval_test", sample_devops_files)

    # 1. Unapproved deployment must raise PermissionError
    with pytest.raises(PermissionError):
        asyncio.run(agent.execute_approved_deployment("approval_test", plan, approved_by_user=False))

    # 2. Approved deployment executes successfully
    result = asyncio.run(agent.execute_approved_deployment("approval_test", plan, approved_by_user=True))
    assert result["status"] == "LIVE"
    assert "vercel" in result["frontend_url"] or "http" in result["frontend_url"]
    assert "render" in result["backend_url"] or "http" in result["backend_url"]


def test_devops_copilot_failure_diagnosis():
    copilot = global_devops_copilot

    # 1. DB connection failure log
    db_logs = [
        "[10:00:01] Starting backend service",
        "[10:00:04] sqlalchemy.exc.OperationalError: could not connect to server: Connection refused",
        "[10:00:05] Missing DATABASE_URL connection string"
    ]
    diag_db = copilot.diagnose_failure("test_proj", db_logs)
    assert diag_db.category == "ENVIRONMENT_CONFIGURATION"
    assert "DATABASE_URL" in diag_db.root_cause or "database" in diag_db.root_cause.lower()

    # 2. Health check failure log
    health_logs = [
        "[10:00:01] Container started on port 8000",
        "[10:00:30] Health check failed: GET /health returned HTTP 404"
    ]
    diag_health = copilot.diagnose_failure("test_proj", health_logs)
    assert diag_health.category == "HEALTH_CHECK_FAILURE"


def test_deployment_rollback_and_memory_persistence(sample_devops_files):
    agent = DevOpsAgent()
    mem_service = global_project_memory_service

    # Record deployment decision in project memory
    mem_service.record_decision(
        project_id="rollback_test_proj",
        decision="Deployed v1 to Vercel and Render",
        rationale="All 48 tests passed and user approved",
        agent_name="DevOpsAgent"
    )

    profile = mem_service.get_project_profile("rollback_test_proj")
    assert profile is not None
    assert any("Deployed v1" in d.decision for d in profile.decisions)


def test_devops_fastapi_rest_endpoints():
    client = TestClient(app)

    # 1. Get deployment plan
    resp_plan = client.post("/api/projects/aiforge-demo/deployment/plan")
    assert resp_plan.status_code == 200
    plan_data = resp_plan.json()
    assert "spec" in plan_data
    assert "readiness" in plan_data
    assert "generated_configs" in plan_data

    # 2. Rejection of unapproved deployment
    resp_unapproved = client.post("/api/projects/aiforge-demo/deployment/deploy", json={
        "approved": False
    })
    assert resp_unapproved.status_code == 400

    # 3. Diagnosis endpoint
    resp_diag = client.post("/api/projects/aiforge-demo/deployment/diagnose", json={
        "logs": ["[ERROR] could not connect to server: Connection refused", "DATABASE_URL is missing"]
    })
    assert resp_diag.status_code == 200
    diag_data = resp_diag.json()
    assert diag_data["category"] == "ENVIRONMENT_CONFIGURATION"

    # 4. Rollback endpoint
    resp_rb = client.post("/api/projects/aiforge-demo/deployment/rollback", json={
        "target_version": "v1"
    })
    assert resp_rb.status_code == 200
    assert resp_rb.json()["status"] == "ROLLED_BACK"
