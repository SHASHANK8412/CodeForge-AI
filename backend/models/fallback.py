import logging
from typing import Dict, Any, List, Callable, Optional

from backend.models.registry import global_model_registry

logger = logging.getLogger("aiforge.models.fallback")


class AutomaticFallbackHandler:
    """
    AutomaticFallbackHandler manages automatic model failovers when a primary model
    encounters a timeout, connection error, or empty output.
    """

    def execute_with_fallback(
        self,
        primary_model: str,
        task_name: str,
        invoke_fn: Callable[[str], Any]
    ) -> Dict[str, Any]:
        candidates = [primary_model] + [m for m in global_model_registry.models.keys() if m != primary_model]

        errors = []
        for model_id in candidates:
            try:
                meta = global_model_registry.models.get(model_id, {})
                if meta.get("status") != "online":
                    continue

                logger.info(f"Attempting execution on model '{model_id}' for task '{task_name}'...")
                res = invoke_fn(model_id)
                if res:
                    return {
                        "status": "success",
                        "used_model": model_id,
                        "was_fallback": model_id != primary_model,
                        "response": res,
                        "attempted_models": errors
                    }
            except Exception as e:
                logger.warning(f"Model '{model_id}' failed for task '{task_name}': {e}")
                errors.append({"model": model_id, "error": str(e)})

        return {
            "status": "failed",
            "used_model": None,
            "was_fallback": True,
            "response": None,
            "attempted_models": errors
        }


# Global AutomaticFallbackHandler Instance
global_fallback_handler = AutomaticFallbackHandler()
