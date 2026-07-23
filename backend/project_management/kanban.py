"""
AIForge Kanban Board Generator
==============================
Organizes tasks into Kanban board columns:
Todo, In Progress, Review, Testing, Done.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_management")


class KanbanBoardGenerator:
    """
    Generates Kanban board columns and task placements.
    """

    def generate_kanban_board(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        columns = {
            "Todo": [],
            "In Progress": [],
            "Review": [],
            "Testing": [],
            "Done": []
        }

        for t in tasks:
            status = t.get("status", "Todo")
            if status in columns:
                columns[status].append(t)
            else:
                columns["Todo"].append(t)

        _logger.info(f"KanbanBoardGenerator: Generated Kanban board with {len(tasks)} tasks.")
        return {
            "columns": columns,
            "total_card_count": len(tasks)
        }


global_kanban_generator = KanbanBoardGenerator()
