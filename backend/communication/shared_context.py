"""
AIForge Shared Project Context
==============================
Provides shared state management, artifact storage, and agent output retrieval across all active agents.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.communication.context")


class SharedProjectContext:
    """
    Centralized shared memory and context manager for agents.
    """

    def __init__(self) -> None:
        self.context: Dict[str, Any] = {
            "project_name": "Food Delivery App",
            "tech_stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL"
            },
            "completed_tasks": ["Planner Setup", "Architecture Spec"],
            "active_tasks": ["Frontend UI Generation", "Backend API Development"],
            "issues": [],
            "artifacts": {},
            "agent_outputs": {},
            "last_updated": time.time()
        }

    def get_context(self) -> Dict[str, Any]:
        return dict(self.context)

    def update_state(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        self.context.update(updates)
        self.context["last_updated"] = time.time()
        _logger.info("SharedProjectContext: Updated project state.")
        return dict(self.context)

    def store_artifact(self, artifact_name: str, content: Any, agent: str = "Agent") -> Dict[str, Any]:
        self.context["artifacts"][artifact_name] = {
            "content": content,
            "created_by": agent,
            "created_at": time.time()
        }
        self.context["last_updated"] = time.time()
        _logger.info(f"SharedProjectContext: Agent '{agent}' stored artifact '{artifact_name}'")
        return self.context["artifacts"][artifact_name]

    def get_artifact(self, artifact_name: str) -> Optional[Dict[str, Any]]:
        return self.context["artifacts"].get(artifact_name)

    def save_agent_output(self, agent_name: str, output: Any) -> None:
        self.context["agent_outputs"][agent_name] = {
            "output": output,
            "timestamp": time.time()
        }
        self.context["last_updated"] = time.time()

    def get_agent_output(self, agent_name: str) -> Optional[Any]:
        data = self.context["agent_outputs"].get(agent_name)
        return data["output"] if data else None

    def add_issue(self, agent: str, issue_description: str, severity: str = "HIGH") -> Dict[str, Any]:
        issue = {
            "id": f"issue_{int(time.time() * 1000)}",
            "agent": agent,
            "description": issue_description,
            "severity": severity,
            "status": "OPEN",
            "timestamp": time.time()
        }
        self.context["issues"].append(issue)
        return issue


global_shared_context = SharedProjectContext()
