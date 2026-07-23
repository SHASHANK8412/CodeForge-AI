"""
AIForge Automated Sprint Roadmap Generator
=========================================
Groups tasks into Sprint 1, Sprint 2, Sprint 3, and Sprint 4 multi-week engineering roadmaps.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_management")


class RoadmapGenerator:
    """
    Generates multi-sprint roadmaps from prioritized task lists.
    """

    def generate_roadmap(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        sprints = {
            "Sprint 1": [t for t in tasks if t.get("category") in ["Database", "Backend"]],
            "Sprint 2": [t for t in tasks if t.get("category") in ["Frontend", "Payments"]],
            "Sprint 3": [t for t in tasks if t.get("category") in ["Notifications", "Admin Panel"]],
            "Sprint 4": [t for t in tasks if t.get("category") in ["Deployment", "Documentation"]]
        }

        # Fallback if categories differ
        if not any(sprints.values()):
            half = len(tasks) // 2
            sprints = {
                "Sprint 1": tasks[:half],
                "Sprint 2": tasks[half:]
            }

        _logger.info("RoadmapGenerator: Generated 4-Sprint Roadmap.")
        return {
            "sprint_roadmap": sprints,
            "total_sprints_count": len(sprints)
        }


global_roadmap_generator = RoadmapGenerator()
