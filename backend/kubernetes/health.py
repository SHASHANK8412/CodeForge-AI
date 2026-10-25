"""
AIForge Day 31 — Kubernetes Health Probe Manager
=================================================
Configures liveness, readiness, and startup probes bound to real application /health endpoints.
"""

import logging
from typing import Dict, Any

from backend.kubernetes.models import K8sHealthProbe

_logger = logging.getLogger("aiforge.kubernetes.health")


class HealthProbeManager:
    """
    Manages Kubernetes health probes.
    """

    def configure_probes(
        self,
        endpoint_path: str = "/health",
        port: int = 8000,
        initial_delay_seconds: int = 10,
        period_seconds: int = 5
    ) -> Dict[str, K8sHealthProbe]:
        probe = K8sHealthProbe(
            path=endpoint_path,
            port=port,
            initial_delay_seconds=initial_delay_seconds,
            period_seconds=period_seconds
        )
        _logger.info(f"[HealthProbeManager] Configured probes for endpoint '{endpoint_path}' on port {port}")
        return {
            "livenessProbe": probe,
            "readinessProbe": probe,
            "startupProbe": probe
        }


global_health_probe_manager = HealthProbeManager()
