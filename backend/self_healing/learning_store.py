"""
AIForge Self-Healing Learning Store
====================================
Knowledge base storing recurring errors, root causes, proven solutions, and occurrence metrics for continuous autonomous improvement.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.self_healing.learning")


class LearningStore:
    """
    Stores failure lessons, root cause patterns, and reusable fixes.
    """

    def __init__(self) -> None:
        self.lessons: Dict[str, Dict[str, Any]] = {
            "lesson_env": {
                "lesson_id": "lesson_env",
                "problem": "Missing Environment Variable",
                "root_cause": "Unset environment key during startup",
                "solution": "Validate .env configuration and provide default fallback before startup",
                "occurrences": 18,
                "success_rate_percentage": 100.0,
                "last_seen": time.time() - 3600
            },
            "lesson_db_pool": {
                "lesson_id": "lesson_db_pool",
                "problem": "Database Connection Timeout",
                "root_cause": "Exhausted connection pool under concurrent load",
                "solution": "Increase pool_size to 20 and enable pool_pre_ping in database connection string",
                "occurrences": 12,
                "success_rate_percentage": 91.6,
                "last_seen": time.time() - 1800
            }
        }

    def record_lesson(
        self,
        problem: str,
        root_cause: str,
        solution: str,
        was_successful: bool = True
    ) -> Dict[str, Any]:
        lesson_key = problem.lower().replace(" ", "_")
        if lesson_key in self.lessons:
            l = self.lessons[lesson_key]
            l["occurrences"] += 1
            l["last_seen"] = time.time()
            _logger.info(f"LearningStore: Updated existing lesson '{problem}' (Occurrences: {l['occurrences']})")
            return l
        else:
            lesson_id = f"lesson_{int(time.time() * 1000)}"
            entry = {
                "lesson_id": lesson_id,
                "problem": problem,
                "root_cause": root_cause,
                "solution": solution,
                "occurrences": 1,
                "success_rate_percentage": 100.0 if was_successful else 0.0,
                "last_seen": time.time()
            }
            self.lessons[lesson_key] = entry
            _logger.info(f"LearningStore: Created new lesson '{problem}'")
            return entry

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        return sorted(list(self.lessons.values()), key=lambda x: x["occurrences"], reverse=True)

    def search_lessons(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            l for l in self.lessons.values()
            if q in l["problem"].lower() or q in l["root_cause"].lower() or q in l["solution"].lower()
        ]


global_learning_store = LearningStore()
