"""
AIForge Day 32 — Infrastructure Providers Submodule
"""
from backend.infrastructure.providers.base import CloudProvider
from backend.infrastructure.providers.aws import global_aws_provider
from backend.infrastructure.providers.azure import global_azure_provider
from backend.infrastructure.providers.gcp import global_gcp_provider
from backend.infrastructure.providers.local import global_local_infra_provider

__all__ = [
    "CloudProvider",
    "global_aws_provider",
    "global_azure_provider",
    "global_gcp_provider",
    "global_local_infra_provider"
]
