import os
import sys
import asyncio
from pathlib import Path

# Ensure PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.deployment.deployment_analyzer import global_deployment_analyzer
from backend.deployment.environment_manager import global_environment_manager
from backend.deployment.providers.local_docker_provider import global_local_docker_provider
from backend.deployment.smoke_tester import global_smoke_tester
from backend.deployment.rollback_manager import global_rollback_manager
from backend.deployment.deployment_orchestrator import global_deployment_orchestrator
from backend.execution.preview_manager import global_preview_manager
from backend.execution.health_checker import global_health_checker


async def run_devops_acceptance():
    print("=" * 70)
    print("AIForge Autonomous DevOps & One-Click Deployment Acceptance Test")
    print("=" * 70)

    proj_dir = Path("./generated_projects/TodoApp").resolve()
    proj_dir.mkdir(parents=True, exist_ok=True)

    files_manifest = {
        "backend/main.py": (
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            "@app.get('/health')\n"
            "def health(): return {'status': 'healthy'}\n"
            "@app.post('/api/auth/login')\n"
            "def login(data: dict): return {'access_token': 'devops_jwt_token_123'}\n"
        ),
        "backend/requirements.txt": "fastapi==0.110.0\nuvicorn==0.28.0\n",
        "frontend/package.json": '{"dependencies": {"react": "^18.2.0"}, "scripts": {"dev": "vite"}}',
        "frontend/src/App.jsx": "import React from 'react'; export default function App(){ return <div>Todo App</div>; }"
    }

    for path, content in files_manifest.items():
        fp = proj_dir / path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")

    # 1. Analyze Deployment
    spec = global_deployment_analyzer.analyze(proj_dir, files_manifest)
    print(f"[OK] [1/7] Deployment Analysis: FE={spec.frontend_tech}, BE={spec.backend_tech}, Envs={spec.required_env_vars}")
    assert spec.backend_port == 8000
    assert spec.health_check_endpoint == "/health"

    # 2. Configure Environment Secrets
    global_environment_manager.configure_environment("TodoApp", {
        "JWT_SECRET": "aiforge_devops_secret_key_32chars_long",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/tododb"
    })
    env_res = global_environment_manager.validate_environment("TodoApp", spec.required_env_vars)
    print(f"[OK] [2/7] Environment Secrets Validated: {env_res.is_valid} (Masked: {env_res.variables['JWT_SECRET'].masked_value})")
    assert env_res.is_valid is True

    # 3. Create Git Checkpoint Tag
    checkpoint = global_rollback_manager.create_deployment_checkpoint(proj_dir)
    print(f"[OK] [3/7] Git Deployment Checkpoint Tag Created: '{checkpoint}'")
    assert checkpoint.startswith("deployment-")

    # 4. Execute Autonomous DevOps Pipeline
    print("[RUN] [4/7] Executing Deployment Orchestrator...")
    record = await global_deployment_orchestrator.deploy_project_async("TodoApp", proj_dir, files_manifest)
    print(f"[OK] [5/7] Pipeline Execution Complete: Status={record.status}, FE={record.frontend_url}, BE={record.backend_url}")
    assert record.status in ["VERIFIED", "RUNNING"]

    # 5. Post-Deployment Smoke Tests
    smoke = await global_smoke_tester.run_smoke_tests_async(record.frontend_url, record.backend_url)
    print(f"[OK] [6/7] Post-Deployment Smoke Tests: {smoke.passed_count}/{smoke.total} PASSED")
    assert smoke.passed is True

    # 6. Verify DEPLOYMENT_REPORT.md Creation
    report_file = proj_dir / "DEPLOYMENT_REPORT.md"
    assert report_file.exists(), "DEPLOYMENT_REPORT.md missing!"
    print(f"[OK] [7/7] DEPLOYMENT_REPORT.md Generated Successfully!")

    print("\n[SUCCESS] ALL AUTONOMOUS DEVOPS & ONE-CLICK DEPLOYMENT ACCEPTANCE TESTS PASSED!\n")


if __name__ == "__main__":
    asyncio.run(run_devops_acceptance())
