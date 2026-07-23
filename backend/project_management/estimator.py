"""
AIForge Task Estimator
======================
Predicts task complexity, estimated time (hours & days), and risk scores.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_management")


class TaskEstimator:
    """
    Estimates task effort, complexity, and risk level.
    """

    def estimate_task(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        category = task_info.get("category", "")
        priority = task_info.get("priority", "MEDIUM")

        if category in ["Database", "Payments", "Backend"]:
            hours = 12.0
            complexity = "Complex"
            risk = "High" if category == "Payments" else "Medium"
        elif category in ["Frontend", "Deployment"]:
            hours = 8.0
            complexity = "Moderate"
            risk = "Medium"
        else:
            hours = 4.0
            complexity = "Simple"
            risk = "Low"

        days = round(hours / 8.0, 1)

        return {
            "task_id": task_info.get("task_id"),
            "estimated_hours": hours,
            "estimated_days": days,
            "complexity": complexity,
            "risk_level": risk
        }


global_task_estimator = TaskEstimator()
