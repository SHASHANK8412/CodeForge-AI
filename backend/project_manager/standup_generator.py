import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class StandupGenerator:
    """
    Compiles AI daily SRE standups mapping Yesterday actions, Today plans, and Blockers impediments.
    """

    def __init__(self) -> None:
        pass

    def generate_standup_report(self, state: Dict[str, Any]) -> str:
        """
        Builds Markdown-ready standup text.
        """
        tasks = state.get("tasks", {})
        
        yesterday = []
        today = []
        blockers = []

        for name, info in tasks.items():
            status = info.get("status")
            if status == "Completed":
                yesterday.append(name)
            elif status == "In Progress" or status == "Pending":
                today.append(name)
            elif status == "Blocked":
                blockers.append(name)

        yesterday_str = ", ".join(yesterday) if yesterday else "None"
        today_str = ", ".join(today) if today else "None"
        blockers_str = ", ".join(blockers) if blockers else "None"

        report = f"""### AI Daily Standup Report

* **Yesterday (Completed)**: {yesterday_str}
* **Today (Active Plan)**: {today_str}
* **Impediments (Blockers)**: {blockers_str}
"""
        _logger.info("Compiled AI daily standup report successfully.")
        return report
