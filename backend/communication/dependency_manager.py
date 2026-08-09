"""
AIForge Dependency Manager
==========================
Orchestrates agent task execution dependencies (Backend APIs, Database Schema, Auth, Env vars, Deployment config),
blocking dependent agent tasks until prerequisite dependencies are resolved.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.communication.dependencies")


class DependencyManager:
    """
    Tracks and enforces inter-agent task execution dependencies.
    """

    def __init__(self) -> None:
        self.dependencies: Dict[str, Dict[str, Any]] = {
            "dep_frontend_backend": {
                "id": "dep_frontend_backend",
                "consumer_agent": "Frontend Agent",
                "prerequisite": "Backend API Endpoints",
                "provider_agent": "Backend Agent",
                "status": "RESOLVED",
                "resolved_at": time.time() - 1800
            },
            "dep_backend_db": {
                "id": "dep_backend_db",
                "consumer_agent": "Backend Agent",
                "prerequisite": "Database Schemas & Migration",
                "provider_agent": "Database Agent",
                "status": "RESOLVED",
                "resolved_at": time.time() - 2400
            },
            "dep_testing_deploy": {
                "id": "dep_testing_deploy",
                "consumer_agent": "DevOps Agent",
                "prerequisite": "Integration Test Suite Passing",
                "provider_agent": "Testing Agent",
                "status": "WAITING",
                "resolved_at": None
            }
        }

    def register_dependency(
        self,
        consumer_agent: str,
        prerequisite: str,
        provider_agent: str
    ) -> Dict[str, Any]:
        dep_id = f"dep_{int(time.time() * 1000)}"
        dep = {
            "id": dep_id,
            "consumer_agent": consumer_agent,
            "prerequisite": prerequisite,
            "provider_agent": provider_agent,
            "status": "WAITING",
            "registered_at": time.time(),
            "resolved_at": None
        }
        self.dependencies[dep_id] = dep
        _logger.info(f"DependencyManager: Registered dependency '{prerequisite}' for '{consumer_agent}' (Provider: '{provider_agent}')")
        return dep

    def resolve_dependency(self, prerequisite_or_id: str) -> List[Dict[str, Any]]:
        resolved_list = []
        for dep in self.dependencies.values():
            if dep["id"] == prerequisite_or_id or prerequisite_or_id.lower() in dep["prerequisite"].lower():
                dep["status"] = "RESOLVED"
                dep["resolved_at"] = time.time()
                resolved_list.append(dep)
                _logger.info(f"DependencyManager: Resolved dependency '{dep['prerequisite']}' for '{dep['consumer_agent']}'")

        return resolved_list

    def is_agent_blocked(self, agent_name: str) -> bool:
        waiting = [
            d for d in self.dependencies.values()
            if d["consumer_agent"].lower() == agent_name.lower() and d["status"] == "WAITING"
        ]
        return len(waiting) > 0

    def get_pending_dependencies(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        deps = list(self.dependencies.values())
        if agent_name:
            deps = [d for d in deps if d["consumer_agent"].lower() == agent_name.lower()]
        return [d for d in deps if d["status"] == "WAITING"]

    def get_all_dependencies(self) -> List[Dict[str, Any]]:
        return list(self.dependencies.values())

    def get_all_dependencies_list(self) -> List[Dict[str, Any]]:
        return list(self.dependencies.values())


global_dependency_manager = DependencyManager()
