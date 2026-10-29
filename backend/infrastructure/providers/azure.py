"""
AIForge Day 32 — Azure Infrastructure Provider
"""
from backend.infrastructure.providers.base import CloudProvider
from backend.infrastructure.terraform.models import CloudProviderConfig, CostEstimate


class AzureCloudProvider(CloudProvider):
    @property
    def provider_name(self) -> str:
        return "Azure"

    def get_config(self) -> CloudProviderConfig:
        return CloudProviderConfig(
            provider_name="Azure",
            is_configured=True,
            region="eastus",
            account_id="sub_azure_123",
            status_message="Azure subscription active."
        )

    def estimate_cost(self, project_id: str) -> CostEstimate:
        return CostEstimate(
            monthly_compute_usd=52.0,
            monthly_database_usd=38.0,
            monthly_redis_usd=18.0,
            monthly_total_usd=108.0,
            is_estimate=True,
            label="ESTIMATE AVAILABLE"
        )


global_azure_provider = AzureCloudProvider()
