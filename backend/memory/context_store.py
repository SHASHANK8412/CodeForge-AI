import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("aiforge.memory.context_store")


class ContextStore:
    """
    ContextStore holds structured project state across all agent pipeline stages:
    planner, architect, frontend, backend, database, reviewer, testing, documentation.
    """

    def __init__(self):
        self._store: Dict[str, Any] = {
            "planner": {},
            "architect": {},
            "frontend": {},
            "backend": {},
            "database": {},
            "reviewer": {},
            "testing": {},
            "documentation": {}
        }

    def set_agent_output(self, agent_name: str, data: Any) -> None:
        """Stores structured output for a specific agent."""
        agent_key = agent_name.lower().strip()
        self._store[agent_key] = data
        logger.info(f"ContextStore updated for agent '{agent_key}'")

    def get_agent_output(self, agent_name: str) -> Any:
        """Retrieves structured output for a specific agent."""
        agent_key = agent_name.lower().strip()
        return self._store.get(agent_key, {})

    def update_agent_output(self, agent_name: str, data: Any) -> None:
        """Updates or merges agent output."""
        agent_key = agent_name.lower().strip()
        existing = self._store.get(agent_key, {})
        if isinstance(existing, dict) and isinstance(data, dict):
            existing.update(data)
            self._store[agent_key] = existing
        else:
            self._store[agent_key] = data

    def delete_agent_output(self, agent_name: str) -> bool:
        """Deletes output for a specific agent."""
        agent_key = agent_name.lower().strip()
        if agent_key in self._store:
            self._store[agent_key] = {}
            return True
        return False

    def get_context(self) -> Dict[str, Any]:
        """Returns the full context store dict."""
        return self._store

    def clear_context(self) -> None:
        """Resets the context store to empty dicts for all agents."""
        self._store = {
            "planner": {},
            "architect": {},
            "frontend": {},
            "backend": {},
            "database": {},
            "reviewer": {},
            "testing": {},
            "documentation": {}
        }

    def extract_shared_stack(self) -> Dict[str, str]:
        """
        Extracts high-level stack choices (Auth, Frontend, Backend, Database)
        from planner and architect outputs for automatic propagation.
        """
        planner_data = self.get_agent_output("planner")
        arch_data = self.get_agent_output("architect")

        shared = {
            "authentication": "JWT",
            "frontend": "React",
            "backend": "FastAPI",
            "database": "PostgreSQL"
        }

        if isinstance(planner_data, dict):
            if "tech_stack" in planner_data:
                ts = planner_data["tech_stack"]
                if isinstance(ts, dict):
                    shared.update(ts)
            if "project_name" in planner_data:
                shared["project_name"] = planner_data["project_name"]

        if isinstance(arch_data, dict):
            if "architecture" in arch_data:
                shared["architecture_style"] = arch_data["architecture"]

        return shared
