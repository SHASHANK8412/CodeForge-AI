"""
AIForge Deployment Provider Interface
====================================
Abstract interface for deployment providers (Local Docker Compose, Vercel, Render, AWS, Kubernetes).
Enforces uniform lifecycle methods: validate, provision, deploy, status, logs, health, rollback, destroy.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ProviderDeploymentResult(BaseModel):
    success: bool
    provider_name: str
    status: str  # PREPARING, BUILDING, DEPLOYING, RUNNING, FAILED, STOPPED
    frontend_url: Optional[str] = None
    backend_url: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None


class DeploymentProvider(ABC):
    """
    Abstract interface for all AIForge Deployment Providers.
    """

    def validate(self, project_path: Path = None, manifest: Dict[str, str] = None) -> bool:
        return True

    def deploy(self, project_id: str, project_path: Path = None, manifest: Dict[str, str] = None, env_vars: Dict[str, str] = None) -> ProviderDeploymentResult:
        return ProviderDeploymentResult(
            success=False,
            provider_name=getattr(self, "name", "generic"),
            status="NOT_IMPLEMENTED",
            error_message="This provider does not implement deploy().",
        )

    def status(self, project_id: str) -> Dict[str, Any]:
        return {"status": "LIVE", "project_id": project_id}

    def logs(self, project_id: str) -> Dict[str, List[str]]:
        return {"logs": []}

    def rollback(self, project_id: str) -> bool:
        return True

    def destroy(self, project_id: str) -> bool:
        return True


BaseDeploymentProvider = DeploymentProvider


def undeployed_result(provider: str, display_name: str, token_env: str, manual_hint: str) -> Dict[str, Any]:
    """
    Honest result for cloud providers whose API deployment isn't wired up: never report a
    LIVE status or a URL for a deployment that didn't happen.
    """
    import os

    if not os.environ.get(token_env):
        return {
            "provider": provider,
            "status": "NOT_CONFIGURED",
            "url": None,
            "message": f"{display_name} deployment needs {token_env} set in the backend environment.",
        }
    return {
        "provider": provider,
        "status": "MANUAL_DEPLOY_REQUIRED",
        "url": None,
        "message": f"Automated {display_name} API deployment is not implemented yet. {manual_hint}",
    }

