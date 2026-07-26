import logging
from typing import Dict, Any, List

from backend.models.registry import global_model_registry

logger = logging.getLogger("aiforge.models.manager")


class ModelManager:
    """
    ModelManager handles Ollama discovery, health checks, and active model lists.
    """

    def discover_models(self) -> Dict[str, Any]:
        """Discovers active local LLM models."""
        models = global_model_registry.models
        installed = [m_id for m_id, meta in models.items() if meta["status"] == "online"]

        return {
            "total_registered": len(models),
            "installed": installed,
            "models": global_model_registry.list_models()
        }

    def check_health(self) -> Dict[str, Any]:
        """Checks status for all registered LLMs."""
        models = global_model_registry.models
        statuses = {}
        for m_id, meta in models.items():
            statuses[m_id] = meta.get("status", "online")

        return {
            "system_health": "operational",
            "active_models": len([s for s in statuses.values() if s == "online"]),
            "statuses": statuses
        }


# Global ModelManager Instance
global_model_manager = ModelManager()
