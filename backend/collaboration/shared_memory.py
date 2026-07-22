"""
Day 43 - Shared Context Memory Store
====================================
Thread-safe and async-safe shared memory accessible by all agents for project context, standards, and schemas.
"""

from typing import Dict, Any, List
import copy


class SharedContextMemory:
    """Shared context memory store accessible to all agents."""

    def __init__(self):
        self._data: Dict[str, Any] = {
            "project_name": "AIForge Application",
            "architecture_style": "FastAPI + React + PostgreSQL Multi-Agent Architecture",
            "coding_standards": {
                "backend_framework": "FastAPI",
                "frontend_framework": "React 18 / Vite",
                "api_prefix": "/api/v1",
                "auth_header": "Authorization: Bearer <jwt_token>",
                "naming_convention_db": "snake_case",
                "naming_convention_api": "snake_case"
            },
            "api_registry": [],
            "db_registry": [],
            "component_registry": []
        }

    def set(self, key: str, value: Any):
        self._data[key] = copy.deepcopy(value)

    def get(self, key: str, default: Any = None) -> Any:
        val = self._data.get(key, default)
        return copy.deepcopy(val) if val is not None else default

    def update_registry(self, category: str, item: Any):
        if category not in self._data:
            self._data[category] = []
        if isinstance(self._data[category], list):
            self._data[category].append(copy.deepcopy(item))

    def get_all(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def clear(self):
        self._data.clear()
        self.__init__()
