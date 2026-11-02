"""
AIForge Day 20 — DeploymentProvider Abstract Base Interface
============================================================
Defines the standard provider abstraction interface for cloud & container platforms:
validate(), build(), deploy(), status(), health(), rollback().
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.devops.models import DeploymentStatus, DeploymentPlan, HealthCheckResult


class DeploymentProvider(ABC):
    """
    Abstract interface for all AIForge deployment providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def validate(self, project_id: str, plan: DeploymentPlan) -> bool:
        pass

    @abstractmethod
    def build(self, project_id: str, plan: DeploymentPlan) -> Dict[str, Any]:
        pass

    @abstractmethod
    def deploy(self, project_id: str, plan: DeploymentPlan) -> DeploymentStatus:
        pass

    @abstractmethod
    def status(self, deployment_id: str) -> DeploymentStatus:
        pass

    @abstractmethod
    def health(self, deployment_id: str) -> HealthCheckResult:
        pass

    @abstractmethod
    def rollback(self, project_id: str, target_version: int) -> DeploymentStatus:
        pass
