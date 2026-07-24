"""
AIForge Day 101 Product Manager Agent
======================================
Responsibilities:
- Analyze user feedback & GitHub issues
- Read feature requests & merge duplicates
- Prioritize backlog based on business value
- Estimate implementation effort
- Recommend automated sprint roadmap
"""

import logging
from typing import Dict, Any, List, Optional

from backend.services.feedback_service import global_feedback_service
from backend.services.roadmap_service import global_roadmap_service

_logger = logging.getLogger("aiforge.agents.product_manager")


class ProductManagerAgent:
    """
    Autonomous Product Manager Agent.
    """

    def analyze_feedback_and_plan(
        self,
        feedback_list: Optional[List[str]] = None,
        github_issues: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        _logger.info("ProductManagerAgent: Running product intelligence analysis...")

        feedback_list = feedback_list or [
            "Dark mode needed",
            "Login is slow",
            "Add notifications",
            "Dashboard crashes",
            "Better mobile support"
        ]

        github_issues = github_issues or [
            "Login broken",
            "Can't sign in",
            "Dashboard crash on load",
            "Need dark theme"
        ]

        # 1. Categorize priority
        categorized = global_feedback_service.categorize_feedback(feedback_list)

        # 2. Merge duplicates
        duplicates = global_feedback_service.detect_duplicate_issues(github_issues)

        # 3. Generate Roadmap
        roadmap = global_roadmap_service.generate_sprint_roadmap(feedback_list)

        return {
            "status": "success",
            "agent_role": "ProductManagerAgent",
            "categorized_priorities": categorized,
            "merged_duplicate_issues": duplicates,
            "sprint_roadmap": roadmap["roadmap"],
            "backlog_summary": roadmap["backlog_queue"]
        }


global_product_manager_agent = ProductManagerAgent()
