import logging
from typing import Dict, Any, List, Optional
from backend.models.capabilities import CapabilityScores, global_capability_scores

logger = logging.getLogger("aiforge.models.registry")


class ModelRegistry:
    """
    ModelRegistry registers installed LLM models, tracks health/availability status,
    and maintains task capability matrices.
    """

    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {
            "qwen2.5-coder": {
                "name": "Qwen 2.5 Coder 14B",
                "provider": "Ollama",
                "status": "online",
                "capabilities": global_capability_scores.DEFAULT_CAPABILITIES["qwen2.5-coder"]
            },
            "deepseek-coder": {
                "name": "DeepSeek Coder V2",
                "provider": "Ollama",
                "status": "online",
                "capabilities": global_capability_scores.DEFAULT_CAPABILITIES["deepseek-coder"]
            },
            "llama3.1": {
                "name": "Llama 3.1 8B Instruct",
                "provider": "Ollama",
                "status": "online",
                "capabilities": global_capability_scores.DEFAULT_CAPABILITIES["llama3.1"]
            },
            "mistral-7b": {
                "name": "Mistral 7B Instruct",
                "provider": "Ollama",
                "status": "online",
                "capabilities": global_capability_scores.DEFAULT_CAPABILITIES["mistral-7b"]
            }
        }

    def list_models() -> List[Dict[str, Any]]:
        """Returns list of registered models with online/offline status."""
        return [
            {
                "id": model_id,
                **meta
            }
            for model_id, meta in self.models.items()
        ]

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self.models.get(model_id)

    def set_status(self, model_id: str, status: str) -> None:
        if model_id in self.models:
            self.models[model_id]["status"] = status

    def update_capabilities(self, model_id: str, updates: Dict[str, int]) -> None:
        if model_id in self.models:
            self.models[model_id]["capabilities"].update(updates)


# Global ModelRegistry Instance
global_model_registry = ModelRegistry()
