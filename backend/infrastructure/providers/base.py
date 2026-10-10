"""
AIForge Day 32 — Cloud Provider Interface
=========================================
Abstract base interface for Infrastructure Cloud Providers (AWS, Azure, GCP, Local).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from backend.infrastructure.terraform.models import CloudProviderConfig, CostEstimate


class CloudProvider(ABC):

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def get_config(self) -> CloudProviderConfig:
        pass


    @abstractmethod
    def estimate_cost(self, project_id: str) -> CostEstimate:
        pass
