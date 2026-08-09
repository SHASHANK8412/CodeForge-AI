"""
AIForge Intelligent Model Selector
===================================
Selects optimal LLM model based on task category (Coding, Architecture, Documentation, Reasoning), cost budgets, and context window requirements.
"""

import logging
from typing import Dict, Any, Optional
from backend.llm.model_registry import global_model_registry

_logger = logging.getLogger("aiforge.llm.selector")


class ModelSelector:
    """
    Selects optimal model per task category.
    """

    TASK_ROUTING_RULES = {
        "coding": "Qwen Coder",
        "frontend": "Qwen Coder",
        "backend": "Qwen Coder",
        "architecture": "DeepSeek Coder",
        "system_design": "DeepSeek Coder",
        "documentation": "Llama 3.x",
        "readme": "Llama 3.x",
        "reasoning": "GPT-4o",
        "complex_logic": "Claude 3.5 Sonnet"
    }

    def select_best_model(self, task_type: str = "general", prompt: str = "") -> Dict[str, Any]:
        task_lower = task_type.lower()
        prompt_lower = prompt.lower()

        # Determine task classification
        if any(k in task_lower or k in prompt_lower for k in ["code", "coding", "coder", "script", "fn", "function", "api"]):
            selected_name = "Qwen Coder"
            category = "Coding"
        elif any(k in task_lower or k in prompt_lower for k in ["arch", "architecture", "design", "blueprint"]):
            selected_name = "DeepSeek Coder"
            category = "Architecture Design"
        elif any(k in task_lower or k in prompt_lower for k in ["doc", "documentation", "readme", "comment"]):
            selected_name = "Llama 3.x"
            category = "Documentation"
        elif any(k in task_lower or k in prompt_lower for k in ["reason", "eval", "review", "complex"]):
            selected_name = "GPT-4o"
            category = "Complex Reasoning"
        else:
            selected_name = "Qwen 2.5"
            category = "General Task"

        metadata = global_model_registry.get_model_metadata(selected_name) or {
            "name": selected_name,
            "provider": "Ollama",
            "supports_code": True,
            "supports_reasoning": True,
            "context_window": 32768,
            "latency": "Low",
            "cost": "Free"
        }

        selection_result = {
            "selected_model": metadata["name"],
            "category": category,
            "provider": metadata["provider"],
            "metadata": metadata,
            "routing_reason": f"Matched task '{category}' to optimal model '{metadata['name']}'"
        }

        _logger.info(f"ModelSelector: {selection_result['routing_reason']}")
        return selection_result


global_model_selector = ModelSelector()
