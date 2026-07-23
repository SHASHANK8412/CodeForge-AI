"""
AIForge Intelligent Model Selector
==================================
Classifies incoming prompts and tasks, evaluating cost, speed, coding score, and historical model memory to route requests automatically.
"""

import logging
from typing import Dict, Any
from backend.llm.model_registry import MODELS
from backend.llm.model_memory import ModelMemory

_logger = logging.getLogger("aiforge.llm")

class ModelSelector:
    """
    Intelligently selects the best LLM model based on task classification and performance memory.
    """

    def __init__(self, memory: ModelMemory = None) -> None:
        if memory is None:
            memory = ModelMemory()
        self.memory = memory

    def classify_task(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["quick fix", "typo", "import", "syntax", "format"]):
            return "quick_fix"
        elif any(w in prompt_lower for w in ["explain", "why", "how to", "documentation"]):
            return "explanation"
        elif any(w in prompt_lower for w in ["architecture", "microservices", "system design", "enterprise"]):
            return "complex_architecture"
        else:
            return "coding"

    def select_model(self, prompt: str, strategy: str = "auto") -> Dict[str, Any]:
        task_type = self.classify_task(prompt)
        
        if strategy == "fast":
            # Priority: Speed score
            model_key = max(MODELS.keys(), key=lambda k: MODELS[k]["speed"])
        elif strategy == "cheap":
            # Priority: Lowest cost per 1k tokens (Local models cost $0.00)
            model_key = min(MODELS.keys(), key=lambda k: (MODELS[k]["cost_per_1k_tokens"], -MODELS[k]["coding"]))
        elif strategy == "accurate":
            # Priority: Highest coding quality score
            model_key = max(MODELS.keys(), key=lambda k: MODELS[k]["quality"])
        else:
            # Auto strategy: Use historical memory preference
            preferred = self.memory.get_preferred_model(task_type)
            if preferred in MODELS:
                model_key = preferred
            else:
                model_key = "qwen"

        selected = MODELS[model_key].copy()
        selected["selected_key"] = model_key
        selected["task_type"] = task_type
        selected["strategy_used"] = strategy
        _logger.info(f"ModelSelector routed task '{task_type}' (strategy='{strategy}') -> Model '{selected['name']}' ({model_key})")
        return selected
