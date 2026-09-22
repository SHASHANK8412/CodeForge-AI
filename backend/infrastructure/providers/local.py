"""
AIForge Day 32 — Local Infrastructure Provider
"""
from backend.infrastructure.providers.base import CloudProvider
from backend.infrastructure.terraform.models import CloudProviderConfig, CostEstimate


class LocalInfrastructureProvider(CloudProvider):
    @property
    def provider_name(self) -> str:
        return "Local"

    def get_config(self) -> CloudProviderConfig:
        return CloudProviderConfig(
            provider_name="Local",
            is_configured=True,
            region="local",
            account_id="localhost",
            status_message="Local Docker / Sandboxed environment active."
        )

    def estimate_cost(self, project_id: str) -> CostEstimate:
        return CostEstimate(
            monthly_compute_usd=0.0,
            monthly_database_usd=0.0,
            monthly_redis_usd=0.0,
            monthly_total_usd=0.0,
            is_estimate=True,
            label="LOCAL ENVIRONMENT ($0.00)"
        )


global_local_infra_provider = LocalInfrastructureProvider()
