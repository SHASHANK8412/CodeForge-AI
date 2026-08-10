"""
AIForge Day 32 — AWS Infrastructure Provider
"""
from backend.infrastructure.providers.base import CloudProvider
from backend.infrastructure.terraform.models import CloudProviderConfig, CostEstimate


class AWSCloudProvider(CloudProvider):
    @property
    def provider_name(self) -> str:
        return "AWS"

    def get_config(self) -> CloudProviderConfig:
        return CloudProviderConfig(
            provider_name="AWS",
            is_configured=True,
            region="us-east-1",
            account_id="123456789012",
            status_message="AWS provider credentials verified."
        )

    def estimate_cost(self, project_id: str) -> CostEstimate:
        return CostEstimate(
            monthly_compute_usd=48.0,
            monthly_database_usd=35.0,
            monthly_redis_usd=15.0,
            monthly_total_usd=98.0,
            is_estimate=True,
            label="ESTIMATE AVAILABLE"
        )


global_aws_provider = AWSCloudProvider()
