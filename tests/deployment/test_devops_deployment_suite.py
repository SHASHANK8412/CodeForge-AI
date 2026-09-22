import os
import sys
import pytest
import asyncio
from pathlib import Path

# Ensure PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.deployment.deployment_analyzer import global_deployment_analyzer
from backend.deployment.environment_manager import global_environment_manager
from backend.deployment.providers.local_docker_provider import global_local_docker_provider
from backend.deployment.smoke_tester import global_smoke_tester
from backend.deployment.rollback_manager import global_rollback_manager
from backend.deployment.deployment_monitor import global_deployment_monitor
from backend.deployment.deployment_orchestrator import global_deployment_orchestrator


class TestAutonomousDevOpsDeployment:

    def test_deployment_analyzer(self, tmp_path):
        manifest = {
            "frontend/package.json": '{"dependencies": {"react": "^18.2.0"}}',
            "backend/main.py": "from fastapi import FastAPI\napp=FastAPI()\nimport os\nsecret = os.getenv('JWT_SECRET')\ndb = os.getenv('DATABASE_URL')"
        }
        spec = global_deployment_analyzer.analyze(tmp_path, manifest)
        assert "JWT_SECRET" in spec.required_env_vars
        assert "DATABASE_URL" in spec.required_env_vars
        assert spec.backend_port == 8000
        assert spec.health_check_endpoint == "/health"

    def test_environment_manager_validation_and_masking(self):
        # Configure env
        global_environment_manager.configure_environment("DevOpsTestApp", {
            "JWT_SECRET": "super_secret_jwt_key_12345",
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb"
        })

        res = global_environment_manager.validate_environment("DevOpsTestApp", ["JWT_SECRET", "DATABASE_URL"])
        assert res.is_valid is True
        assert res.variables["JWT_SECRET"].masked_value != "super_secret_jwt_key_12345"
        assert "••••" in res.variables["JWT_SECRET"].masked_value

    def test_rollback_checkpoint_creation(self, tmp_path):
        tag = global_rollback_manager.create_deployment_checkpoint(tmp_path)
        assert "deployment-" in tag

        entry = global_rollback_manager.trigger_rollback(reason="Test rollback", project_path=tmp_path)
        assert entry["status"] == "RESTORED"

    def test_deployment_monitor_incident(self):
        inc = global_deployment_monitor.record_incident("DevOpsTestApp", "500 Internal Error", "http://localhost:8000/api/fail")
        assert inc.incident_id.startswith("inc_")
        assert inc.project_id == "DevOpsTestApp"
        assert inc.status == "OPEN"

    @pytest.mark.asyncio
    async def test_orchestrator_deployment_pipeline(self, tmp_path):
        proj_dir = tmp_path / "DevOpsE2EApp"
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "backend").mkdir(parents=True, exist_ok=True)
        (proj_dir / "backend" / "main.py").write_text("from fastapi import FastAPI\napp=FastAPI()\n@app.get('/health')\ndef health(): return {'status': 'ok'}", encoding="utf-8")
        (proj_dir / "backend" / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")

        manifest = {
            "backend/main.py": (proj_dir / "backend" / "main.py").read_text(),
            "backend/requirements.txt": (proj_dir / "backend" / "requirements.txt").read_text()
        }

        # Configure environment secrets
        global_environment_manager.configure_environment("DevOpsE2EApp", {
            "JWT_SECRET": "secret_key_32chars_long_for_devops",
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/appdb"
        })

        record = await global_deployment_orchestrator.deploy_project_async("DevOpsE2EApp", proj_dir, manifest)
        assert record.project_id == "DevOpsE2EApp"
        assert record.status in ["VERIFIED", "RUNNING"]
        assert record.git_checkpoint is not None

        # Clean up
        global_local_docker_provider.destroy("DevOpsE2EApp")
