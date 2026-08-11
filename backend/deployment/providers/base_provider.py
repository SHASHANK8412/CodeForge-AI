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

    @abstractmethod
    def validate(self, project_path: Path, manifest: Dict[str, str]) -> bool:
        pass

    @abstractmethod
    def deploy(self, project_id: str, project_path: Path, manifest: Dict[str, str], env_vars: Dict[str, str]) -> ProviderDeploymentResult:
        pass

    @abstractmethod
    def status(self, project_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def logs(self, project_id: str) -> Dict[str, List[str]]:
        pass

    @abstractmethod
    def rollback(self, project_id: str) -> bool:
        pass

    @abstractmethod
    def destroy(self, project_id: str) -> bool:
        pass
