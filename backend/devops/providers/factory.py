"""
AIForge Day 20 — Deployment Provider Factory
=============================================
Instantiates and returns the appropriate DeploymentProvider (Docker, Render, Vercel, AWS, etc.).
"""

from backend.devops.providers.base import DeploymentProvider
from backend.devops.providers.docker import global_local_docker_provider
from backend.devops.providers.kubernetes import global_kubernetes_provider


class DeploymentProviderFactory:
    """
    Factory for deployment provider abstraction (Docker, Kubernetes).
    """

    @staticmethod
    def get_provider(provider_name: str = "Docker") -> DeploymentProvider:
        p_lower = provider_name.lower()
        if "k8s" in p_lower or "kube" in p_lower:
            return global_kubernetes_provider
        if "docker" in p_lower or "local" in p_lower:
            return global_local_docker_provider

        # Default fallback to LocalDockerProvider
        return global_local_docker_provider



global_provider_factory = DeploymentProviderFactory()
