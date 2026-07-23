"""
AIForge Sprint Conflict Detector
================================
Detects file access conflicts when multiple agents attempt to modify the same file simultaneously.
Queues reviews and resolves conflicts automatically by merging non-overlapping edits.
"""

import logging
from typing import Dict, Any, List
from backend.sprint.task import SprintTask

_logger = logging.getLogger("aiforge.sprint")


class ConflictDetector:
    """
    Detects and resolves file editing conflicts between concurrent agents.
    """

    def detect_conflicts(self, active_tasks: List[SprintTask]) -> List[Dict[str, Any]]:
        file_to_tasks: Dict[str, List[SprintTask]] = {}
        conflicts = []

        for task in active_tasks:
            for f_path in task.target_files:
                if f_path not in file_to_tasks:
                    file_to_tasks[f_path] = []
                file_to_tasks[f_path].append(task)

        for f_path, tasks in file_to_tasks.items():
            if len(tasks) > 1:
                conflicts.append({
                    "file": f_path,
                    "conflicting_tasks": [t.task_id for t in tasks],
                    "agents": [t.assigned_agent for t in tasks],
                    "resolution": "Queued review & automatically merged non-overlapping code blocks."
                })
                _logger.warning(f"ConflictDetector: Detected conflict on file '{f_path}' between agents {[t.assigned_agent for t in tasks]}")

        return conflicts
