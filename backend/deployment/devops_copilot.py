"""
AIForge DevOps Copilot Module
=============================
AI-assisted failure analysis engine for deployments, builds, and health checks.
Inspects logs, configs, and failure signals to identify root cause and recommend fixes.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.deployment.copilot")


class DevOpsDiagnosis(BaseModel):
    category: str
    root_cause: str
    confidence: float
    affected_components: List[str]
    recommended_action: str
    suggested_env_fix: Optional[Dict[str, str]] = None
    suggested_code_patch: Optional[str] = None


class DevOpsCopilot:
    """
    Analyzes deployment failures and suggests targeted fixes.
    """

    def diagnose_failure(
        self,
        project_id: str,
        logs: List[str],
        error_message: str = "",
        spec_data: Optional[Dict[str, Any]] = None
    ) -> DevOpsDiagnosis:
        combined_logs = "\n".join(logs) + "\n" + error_message
        lower_logs = combined_logs.lower()

        # 1. Missing Database / Connection String Issue
        if "database_url" in lower_logs or "connection refused" in lower_logs or "could not connect to server" in lower_logs or "password authentication failed" in lower_logs:
            return DevOpsDiagnosis(
                category="ENVIRONMENT_CONFIGURATION",
                root_cause="Production database connection failed or DATABASE_URL environment variable is missing/invalid.",
                confidence=0.94,
                affected_components=["backend", "database"],
                recommended_action="Configure a valid DATABASE_URL in the production environment settings.",
                suggested_env_fix={"DATABASE_URL": "postgresql://user:password@neon-pooler.neon.tech/appdb"}
            )

        # 2. Health Check Timeout / Missing Health Route
        if "health check failed" in lower_logs or "health" in lower_logs and ("404" in lower_logs or "timeout" in lower_logs or "timed out" in lower_logs):
            return DevOpsDiagnosis(
                category="HEALTH_CHECK_FAILURE",
                root_cause="Container started but the health check probe (/health or /api/health) returned 404 or did not respond within the timeout threshold.",
                confidence=0.88,
                affected_components=["backend", "health_checker"],
                recommended_action="Ensure FastAPI or Express exposes a lightweight GET /health endpoint returning HTTP 200 {'status': 'healthy'}.",
                suggested_code_patch="@app.get('/health')\ndef health_check():\n    return {'status': 'healthy'}"
            )

        # 3. Port Binding / Host Mismatch
        if "address already in use" in lower_logs or "eaddrinuse" in lower_logs or "bind failed" in lower_logs:
            return DevOpsDiagnosis(
                category="PORT_BINDING",
                root_cause="Web service failed to bind to the dynamic cloud provider PORT environment variable.",
                confidence=0.91,
                affected_components=["backend", "docker"],
                recommended_action="Update startCommand or Docker CMD to bind to 0.0.0.0 and listen on the $PORT environment variable provided by the host.",
                suggested_code_patch="uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
            )

        # 4. Dependency / Build Failure
        if "modulenotfounderror" in lower_logs or "cannot find module" in lower_logs or "pip install" in lower_logs or "npm error" in lower_logs:
            return DevOpsDiagnosis(
                category="DEPENDENCY_BUILD_FAILURE",
                root_cause="Missing required runtime package or broken build compilation.",
                confidence=0.89,
                affected_components=["frontend" if "npm" in lower_logs else "backend"],
                recommended_action="Review package manifest (requirements.txt or package.json) to ensure all imported dependencies are listed.",
                suggested_code_patch=None
            )

        # Generic Diagnosis Fallback
        return DevOpsDiagnosis(
            category="GENERAL_DEPLOYMENT_ERROR",
            root_cause="Service startup was interrupted. Inspect detailed application logs for unhandled runtime exceptions.",
            confidence=0.75,
            affected_components=["backend"],
            recommended_action="Review full stderr logs and verify that all required environment variables are set.",
            suggested_code_patch=None
        )


global_devops_copilot = DevOpsCopilot()
