"""
AIForge Autonomous Deployment Orchestrator
==========================================
Coordinates the entire DevOps Deployment Engine:
- Pre-deployment Gates & Security Audit
- Environment Secret Validation & Masking
- Git Deployment Checkpoint Tags
- Containerized Build & Local Docker Provider Execution
- Empirical Health Checks & Post-Deployment Smoke Tests
- Autonomous Deployment Self-Healing & Instant Rollbacks
- DEPLOYMENT_REPORT.md Generation & Deployment History Recording
"""

import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.deployment.deployment_analyzer import global_deployment_analyzer, DeploymentSpec
from backend.deployment.environment_manager import global_environment_manager
from backend.deployment.providers.local_docker_provider import global_local_docker_provider
from backend.execution.health_checker import global_health_checker
from backend.deployment.smoke_tester import global_smoke_tester, SmokeTestResult
from backend.deployment.rollback_manager import global_rollback_manager
from backend.deployment.deployment_monitor import global_deployment_monitor
from backend.security.security_agent import SecurityAgent
global_security_agent = SecurityAgent()

_logger = logging.getLogger("aiforge.deployment.orchestrator")


class DeploymentRecord(BaseModel):
    deployment_id: str
    project_id: str
    status: str = "QUEUED"  # QUEUED, PREPARING, BUILDING, DEPLOYING, STARTING, HEALTH_CHECK, SMOKE_TEST, SECURITY_CHECK, VERIFIED, FAILED, DEPLOYMENT_BLOCKED, ROLLING_BACK, ROLLED_BACK
    frontend_url: Optional[str] = None
    backend_url: Optional[str] = None
    git_checkpoint: Optional[str] = None
    duration_seconds: float = 0.0
    smoke_results: Optional[SmokeTestResult] = None
    logs: List[str] = Field(default_factory=list)
    missing_secrets: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class DeploymentOrchestrator:
    """
    Autonomous DevOps Deployment Orchestrator.
    """

    def __init__(self):
        self._history: List[DeploymentRecord] = []

    def _log(self, record: DeploymentRecord, msg: str):
        ts = time.strftime("%H:%M:%S")
        record.logs.append(f"[{ts}] {msg}")
        _logger.info(f"DeploymentOrchestrator [{record.deployment_id}]: {msg}")

    async def deploy_project_async(
        self,
        project_id: str,
        project_path: Path,
        files_manifest: Dict[str, str]
    ) -> DeploymentRecord:
        dep_id = f"deploy-{int(time.time() * 1000)}"
        record = DeploymentRecord(deployment_id=dep_id, project_id=project_id)
        self._history.insert(0, record)

        start_t = time.time()
        record.status = "PREPARING"
        self._log(record, f"Starting Autonomous DevOps Deployment for '{project_id}'...")

        # 1. Deployment Analysis
        spec = global_deployment_analyzer.analyze(project_path, files_manifest)
        self._log(record, f"Analyzed project: FE={spec.frontend_tech}, BE={spec.backend_tech}, Required Envs={spec.required_env_vars}")

        # 2. Environment Secret Validation Gate
        env_res = global_environment_manager.validate_environment(project_id, spec.required_env_vars)
        if not env_res.is_valid:
            record.status = "DEPLOYMENT_BLOCKED"
            record.missing_secrets = env_res.missing_required_vars
            self._log(record, f"🔴 DEPLOYMENT BLOCKED — Missing required secrets: {env_res.missing_required_vars}")
            return record

        # 3. DevSecOps Security Audit
        record.status = "SECURITY_CHECK"
        self._log(record, "Performing DevSecOps security audit...")
        remedied_files, sec_report = global_security_agent.scan_and_remedy(files_manifest)
        if sec_report.get("vulnerabilities_found", 0) > 10:
            record.status = "DEPLOYMENT_BLOCKED"
            self._log(record, f"🔴 DEPLOYMENT BLOCKED — Excessive un-remedied security vulnerabilities detected.")
            return record

        # 4. Git Deployment Checkpoint
        record.status = "BUILDING"
        checkpoint_tag = global_rollback_manager.create_deployment_checkpoint(project_path)
        record.git_checkpoint = checkpoint_tag
        self._log(record, f"Created Git deployment checkpoint: '{checkpoint_tag}'")

        # 5. Execute Provider Deployment
        record.status = "DEPLOYING"
        self._log(record, "Packaging container artifacts and launching services...")
        clean_envs = {k: v.value for k, v in env_res.variables.items() if v.is_configured}
        prov_res = global_local_docker_provider.deploy(project_id, project_path, files_manifest, clean_envs)

        if not prov_res.success:
            record.status = "FAILED"
            self._log(record, f"🔴 Deployment provider failed: {prov_res.stderr}")
            return record

        record.frontend_url = prov_res.frontend_url
        record.backend_url = prov_res.backend_url

        # 6. Empirical Health Check
        record.status = "HEALTH_CHECK"
        self._log(record, "Probing backend and frontend health endpoints...")
        be_health = await global_health_checker.wait_until_healthy("backend", f"{record.backend_url}{spec.health_check_endpoint}", max_attempts=12)
        fe_health = await global_health_checker.wait_until_healthy("frontend", record.frontend_url, max_attempts=12)

        if not be_health.is_healthy or not fe_health.is_healthy:
            self._log(record, f"⚠ Health check failed (Backend: {be_health.status_code}, Frontend: {fe_health.status_code}). Triggering rollback...")
            record.status = "ROLLING_BACK"
            global_rollback_manager.trigger_rollback(
                reason=f"Health check failed (Backend: {be_health.error_message})",
                project_path=project_path
            )
            record.status = "ROLLED_BACK"
            global_deployment_monitor.record_incident(project_id, f"Health Check Failure on {spec.health_check_endpoint}", record.backend_url)
            return record

        # 7. Post-Deployment Smoke Tests
        record.status = "SMOKE_TEST"
        self._log(record, "Running post-deployment empirical HTTP smoke tests...")
        smoke_res = await global_smoke_tester.run_smoke_tests_async(record.frontend_url, record.backend_url)
        record.smoke_results = smoke_res

        if not smoke_res.passed:
            self._log(record, f"⚠ Post-deployment smoke tests failed ({smoke_res.failed_count} failed). Triggering rollback...")
            record.status = "ROLLING_BACK"
            global_rollback_manager.trigger_rollback(
                reason="Post-deployment smoke tests failed",
                project_path=project_path
            )
            record.status = "ROLLED_BACK"
            global_deployment_monitor.record_incident(project_id, "Smoke Tests Failed", record.backend_url)
            return record

        # 8. Deployment Success Verification
        record.status = "VERIFIED"
        record.duration_seconds = round(time.time() - start_t, 2)
        self._log(record, f"🟢 DEPLOYMENT VERIFIED — Available at Frontend: {record.frontend_url}, Backend: {record.backend_url} (Duration: {record.duration_seconds}s)")

        # 9. Generate DEPLOYMENT_REPORT.md
        self._write_deployment_report(project_path, record)

        return record

    def _write_deployment_report(self, project_path: Path, record: DeploymentRecord):
        content = (
            f"# AIForge Autonomous Deployment Report\n\n"
            f"**Deployment ID**: `{record.deployment_id}`\n"
            f"**Project**: `{record.project_id}`\n"
            f"**Status**: `{record.status}`\n"
            f"**Git Checkpoint**: `{record.git_checkpoint}`\n"
            f"**Frontend URL**: [{record.frontend_url}]({record.frontend_url})\n"
            f"**Backend URL**: [{record.backend_url}]({record.backend_url})\n"
            f"**Duration**: `{record.duration_seconds}s`\n\n"
            f"## Smoke Test Results\n"
            f"- **Passed**: {record.smoke_results.passed_count if record.smoke_results else 0}/{record.smoke_results.total if record.smoke_results else 0}\n\n"
            f"## Deployment Logs\n"
            f"```text\n" + "\n".join(record.logs) + "\n```\n"
        )
        try:
            (project_path / "DEPLOYMENT_REPORT.md").write_text(content, encoding="utf-8")
        except Exception:
            pass

    def get_history(self) -> List[DeploymentRecord]:
        return list(self._history)


global_deployment_orchestrator = DeploymentOrchestrator()
