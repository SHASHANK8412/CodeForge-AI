import logging
from typing import Dict, Any, Optional

from backend.models.registry import global_model_registry

logger = logging.getLogger("aiforge.models.router")


class IntelligentRouter:
    """
    IntelligentRouter selects the best LLM model for each specialized agent task
    based on task type, capability ratings, and online status.
    """

    DEFAULT_ROUTING_TABLE: Dict[str, str] = {
        "planner": "llama3.1",
        "planning": "llama3.1",
        "architect": "deepseek-coder",
        "architecture": "deepseek-coder",
        "backend": "qwen2.5-coder",
        "frontend": "qwen2.5-coder",
        "database": "deepseek-coder",
        "documentation": "llama3.1",
        "reviewer": "deepseek-coder",
        "security": "deepseek-coder",
        "testing": "qwen2.5-coder"
    }

    def route_task(self, task_name: str, user_override: Optional[str] = None) -> Dict[str, Any]:
        """Routes a task to the highest scoring available model."""
        task_key = task_name.lower().strip()

        # 1. User Override Priority
        if user_override and user_override in global_model_registry.models:
            model_info = global_model_registry.models[user_override]
            if model_info["status"] == "online":
                return {
                    "task": task_name,
                    "selected_model": user_override,
                    "model_name": model_info["name"],
                    "reason": f"Explicit User Override to '{user_override}'",
                    "score": model_info["capabilities"].get(task_key, 9)
                }

        # 2. Preferred Routing Table Match
        preferred_id = self.DEFAULT_ROUTING_TABLE.get(task_key, "qwen2.5-coder")
        pref_meta = global_model_registry.models.get(preferred_id)

        if pref_meta and pref_meta.get("status") == "online":
            return {
                "task": task_name,
                "selected_model": preferred_id,
                "model_name": pref_meta["name"],
                "reason": f"Optimal capability score for task '{task_key}'",
                "score": pref_meta["capabilities"].get(task_key, 9)
            }

        # 3. Dynamic Score Selection Fallback
        best_id = "qwen2.5-coder"
        best_score = -1

        for m_id, meta in global_model_registry.models.items():
            if meta.get("status") == "online":
                sc = meta["capabilities"].get(task_key, 7)
                if sc > best_score:
                    best_score = sc
                    best_id = m_id

        meta_res = global_model_registry.models[best_id]
        return {
            "task": task_name,
            "selected_model": best_id,
            "model_name": meta_res["name"],
            "reason": f"Highest available capability rating ({best_score}/10)",
            "score": best_score
        }


# Global IntelligentRouter Instance
global_intelligent_router = IntelligentRouter()
