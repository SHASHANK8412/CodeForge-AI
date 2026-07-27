"""
AIForge LLM Model Registry
==========================
Stores metadata, capabilities, context windows, providers, latency profiles, and cost metrics for supported LLMs:
- Qwen 2.5
- Qwen Coder
- DeepSeek Coder
- Llama 3.x
- Mistral
- Gemma
- GPT-4o
- Claude 3.5 Sonnet
"""

from typing import Dict, Any, List, Optional


class ModelRegistry:
    """
    Registry maintaining metadata for all supported LLM models.
    """

    def __init__(self) -> None:
        self.models: Dict[str, Dict[str, Any]] = {
            "Qwen2.5": {
                "id": "qwen2.5",
                "name": "Qwen 2.5",
                "provider": "Ollama",
                "supports_code": True,
                "supports_reasoning": True,
                "context_window": 32768,
                "latency": "Low",
                "cost": "Free",
                "status": "Available"
            },
            "QwenCoder": {
                "id": "qwen_coder",
                "name": "Qwen Coder",
                "provider": "Ollama",
                "supports_code": True,
                "supports_reasoning": False,
                "context_window": 32768,
                "latency": "Low",
                "cost": "Free",
                "status": "Available"
            },
            "DeepSeekCoder": {
                "id": "deepseek_coder",
                "name": "DeepSeek Coder",
                "provider": "Ollama",
                "supports_code": True,
                "supports_reasoning": True,
                "context_window": 64536,
                "latency": "Medium",
                "cost": "Free",
                "status": "Available"
            },
            "Llama3": {
                "id": "llama3",
                "name": "Llama 3.x",
                "provider": "Ollama",
                "supports_code": False,
                "supports_reasoning": True,
                "context_window": 8192,
                "latency": "Low",
                "cost": "Free",
                "status": "Available"
            },
            "Mistral": {
                "id": "mistral",
                "name": "Mistral 7B",
                "provider": "Ollama",
                "supports_code": True,
                "supports_reasoning": False,
                "context_window": 8192,
                "latency": "Low",
                "cost": "Free",
                "status": "Available"
            },
            "Gemma": {
                "id": "gemma",
                "name": "Gemma 7B",
                "provider": "Ollama",
                "supports_code": False,
                "supports_reasoning": False,
                "context_window": 8192,
                "latency": "Low",
                "cost": "Free",
                "status": "Available"
            },
            "GPT4o": {
                "id": "gpt4o",
                "name": "GPT-4o",
                "provider": "OpenAI API",
                "supports_code": True,
                "supports_reasoning": True,
                "context_window": 128000,
                "latency": "Medium",
                "cost": "$0.005/1K",
                "status": "Available"
            },
            "Claude3.5": {
                "id": "claude3.5",
                "name": "Claude 3.5 Sonnet",
                "provider": "Anthropic API",
                "supports_code": True,
                "supports_reasoning": True,
                "context_window": 200000,
                "latency": "Medium",
                "cost": "$0.003/1K",
                "status": "Available"
            }
        }

    def get_all_models(self) -> List[Dict[str, Any]]:
        return list(self.models.values())

    def get_model_metadata(self, model_name: str) -> Optional[Dict[str, Any]]:
        # Match by name or key
        for k, v in self.models.items():
            if k.lower() == model_name.lower() or v["name"].lower() == model_name.lower() or v["id"].lower() == model_name.lower():
                return v
        return None

    def get_models_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        if capability == "code":
            return [m for m in self.models.values() if m["supports_code"]]
        elif capability == "reasoning":
            return [m for m in self.models.values() if m["supports_reasoning"]]
        return list(self.models.values())


global_model_registry = ModelRegistry()
