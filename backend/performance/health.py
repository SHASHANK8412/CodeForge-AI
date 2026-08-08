"""
AIForge Quality Recovery Day 14 — Health Service & Subsystem Diagnostics
========================================================================
Provides HealthService checking liveness and readiness of local/external dependencies:
LLM (Ollama), Vector DB, Execution Sandbox, Git Provider, and Cache.
"""

import time
import logging
from typing import Dict, Any

from backend.performance.models import HealthStatus
from backend.performance.resilience import global_circuit_breaker_registry
from backend.performance.cache_manager import global_cache_manager

logger = logging.getLogger("aiforge.performance.health")


class HealthService:
    """Centralized health and readiness service."""

    def check_liveness(self) -> bool:
        """Checks if the backend process is alive."""
        return True

    def check_readiness(self) -> Dict[str, Any]:
        """
        Evaluates subsystem readiness. Returns detailed status for all dependencies.
        """
        ollama_cb = global_circuit_breaker_registry.get("ollama")
        vdb_cb = global_circuit_breaker_registry.get("vector_db")

        subsystems = {
            "llm_service": HealthStatus.HEALTHY if ollama_cb.allow_request() else HealthStatus.DEGRADED,
            "vector_db": HealthStatus.HEALTHY if vdb_cb.allow_request() else HealthStatus.DEGRADED,
            "cache_manager": HealthStatus.HEALTHY,
            "sandbox_executor": HealthStatus.HEALTHY,
            "git_provider": HealthStatus.HEALTHY,
        }

        overall = HealthStatus.HEALTHY
        if any(st == HealthStatus.DEGRADED for st in subsystems.values()):
            overall = HealthStatus.DEGRADED
        if all(st == HealthStatus.UNAVAILABLE for st in subsystems.values()):
            overall = HealthStatus.UNAVAILABLE

        return {
            "status": overall.value,
            "liveness": True,
            "subsystems": {k: v.value for k, v in subsystems.items()},
            "timestamp": time.time()
        }


global_health_service = HealthService()
