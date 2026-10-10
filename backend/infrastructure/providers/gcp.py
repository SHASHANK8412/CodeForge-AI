"""
AIForge Day 32 — GCP Infrastructure Provider
"""
from backend.infrastructure.providers.base import CloudProvider
from backend.infrastructure.terraform.models import CloudProviderConfig, CostEstimate


class GCPCloudProvider(CloudProvider):
    @property
    def provider_name(self) -> str:
        return "GCP"

    def get_config(self) -> CloudProviderConfig:
        return CloudProviderConfig(
            provider_name="GCP",
            is_configured=True,
            region="us-central1",
            account_id="proj-gcp-999",
            status_message="GCP project credentials active."
        )

    def estimate_cost(self, project_id: str) -> CostEstimate:
        return CostEstimate(
            monthly_compute_usd=44.0,
            monthly_database_usd=32.0,
            monthly_redis_usd=14.0,
            monthly_total_usd=90.0,
            is_estimate=True,
            label="ESTIMATE AVAILABLE"
        )


global_gcp_provider = GCPCloudProvider()
