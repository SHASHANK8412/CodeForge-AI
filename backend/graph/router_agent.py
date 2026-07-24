"""
AIForge Conditional Agent Router
================================
Evaluates user prompt complexity to skip unnecessary agent nodes:
- Simple UI Request -> Skip Database & Backend heavy steps
- Simple API Request -> Skip Frontend heavy steps
- Full-Stack Request -> Execute full parallel workflow
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.router")


class ConditionalWorkflowRouter:
    """
    Conditional Workflow Router Agent.
    """

    def route_workflow(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower()
        _logger.info(f"ConditionalWorkflowRouter: Routing workflow for prompt '{prompt}'...")

        if any(w in p_lower for w in ["ui only", "landing page", "component only", "css layout", "button"]):
            required_agents = ["planner", "architect", "frontend", "documentation"]
            skipped_agents = ["backend", "database", "testing"]
            workflow_type = "frontend_only"
        elif any(w in p_lower for w in ["api only", "backend only", "fastapi route", "sql query", "microservice"]):
            required_agents = ["planner", "architect", "backend", "database", "testing", "documentation"]
            skipped_agents = ["frontend"]
            workflow_type = "backend_only"
        else:
            required_agents = ["planner", "architect", "frontend", "backend", "database", "reviewer", "testing", "documentation"]
            skipped_agents = []
            workflow_type = "full_stack"

        return {
            "prompt": prompt,
            "workflow_type": workflow_type,
            "required_agents": required_agents,
            "skipped_agents": skipped_agents,
            "estimated_time_saving_pct": 0 if workflow_type == "full_stack" else 40
        }


global_workflow_router = ConditionalWorkflowRouter()
