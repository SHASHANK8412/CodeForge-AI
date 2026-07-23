"""
AIForge Model Memory & Historical Performance Tracker
=====================================================
Tracks accuracy, latency, quality scores, and cost metrics by task type to inform routing decisions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.llm")

class ModelMemory:
    """
    Persists model performance metrics per task type across project executions.
    """

    def __init__(self, memory_path: str = None) -> None:
        if memory_path is None:
            memory_path = str(Path(__file__).resolve().parent / "model_memory.json")
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_memory()

    def _init_memory(self) -> None:
        if not self.memory_path.exists() or self.memory_path.stat().st_size == 0:
            default_data = {
                "coding": {"preferred": "deepseek", "qwen_score": 92, "deepseek_score": 98, "gpt_score": 99},
                "quick_fix": {"preferred": "qwen", "qwen_score": 95, "deepseek_score": 90, "gpt_score": 94},
                "explanation": {"preferred": "gpt", "qwen_score": 85, "deepseek_score": 92, "gpt_score": 98},
                "complex_architecture": {"preferred": "gpt", "qwen_score": 88, "deepseek_score": 94, "gpt_score": 99},
                "history": []
            }
            self._save(default_data)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _logger.error(f"Failed to load model_memory.json: {e}")
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to write model_memory.json: {e}")

    def record_performance(self, task_type: str, model_key: str, latency: float, quality_score: float, cost: float) -> None:
        data = self._load()
        if "history" not in data:
            data["history"] = []
            
        entry = {
            "task_type": task_type,
            "model": model_key,
            "latency": latency,
            "quality_score": quality_score,
            "cost": cost
        }
        data["history"].append(entry)

        # Update preferred model for task category if quality score is high
        if task_type in data:
            current_pref = data[task_type].get("preferred")
            score_key = f"{model_key}_score"
            data[task_type][score_key] = int(quality_score)
            
            # Simple reinforcement: if current model outperforms previous best, update preferred
            prev_best_score = data[task_type].get(f"{current_pref}_score", 0)
            if quality_score > prev_best_score:
                data[task_type]["preferred"] = model_key

        self._save(data)

    def get_preferred_model(self, task_type: str) -> str:
        data = self._load()
        if task_type in data:
            return data[task_type].get("preferred", "qwen")
        return "qwen"

    def get_all_memory(self) -> Dict[str, Any]:
        return self._load()
