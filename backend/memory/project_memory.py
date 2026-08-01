"""
AIForge Persistent Project Memory Engine
========================================
Maintains structured, thread-safe, persistent state across all pipeline stages:
- Generated Files & Folder Structure
- Components, Routes, Models, Schemas
- API Contracts & Endpoints
- Dependencies & Environment Variables
- Agent Decisions & Execution Trace
Future agents query and reuse this memory to eliminate duplicate code and ensure architecture consistency.
"""

import logging
from typing import Dict, Any, List, Optional
from threading import Lock

_logger = logging.getLogger("aiforge.memory.project_memory")


class ProjectMemoryStore:
    """
    Thread-safe persistent memory store for an autonomous project build.
    """

    def __init__(self, project_name: str = "Untitled Project"):
        self.project_name = project_name
        self._lock = Lock()
        self._memory: Dict[str, Any] = {
            "project_name": project_name,
            "architecture": {},
            "folder_structure": {},
            "technology_stack": {},
            "generated_files": {},
            "api_contracts": [],
            "database_entities": [],
            "dependencies": {"frontend": [], "backend": []},
            "environment_variables": {},
            "agent_decisions": [],
            "logs": [],
        }

    def update_architecture(self, architecture: Dict[str, Any], tech_stack: Dict[str, str], folder_structure: Dict[str, Any]) -> None:
        with self._lock:
            self._memory["architecture"] = architecture
            self._memory["technology_stack"] = tech_stack
            self._memory["folder_structure"] = folder_structure
            _logger.info(f"ProjectMemoryStore: Updated architecture for '{self.project_name}'")

    def save_file(self, path: str, content: str, purpose: str = "") -> None:
        with self._lock:
            self._memory["generated_files"][path] = {
                "path": path,
                "content": content,
                "purpose": purpose
            }
            _logger.info(f"ProjectMemoryStore: Saved file '{path}' ({len(content)} bytes)")

    def get_file(self, path: str) -> Optional[str]:
        with self._lock:
            file_obj = self._memory["generated_files"].get(path)
            return file_obj["content"] if file_obj else None

    def get_all_generated_files(self) -> Dict[str, str]:
        with self._lock:
            return {p: info["content"] for p, info in self._memory["generated_files"].items()}

    def add_api_contract(self, endpoint: str, method: str, summary: str, request_schema: Dict[str, Any] = None, response_schema: Dict[str, Any] = None) -> None:
        with self._lock:
            contract = {
                "endpoint": endpoint,
                "method": method,
                "summary": summary,
                "request_schema": request_schema or {},
                "response_schema": response_schema or {}
            }
            self._memory["api_contracts"].append(contract)

    def add_dependency(self, target: str, package_name: str) -> None:
        with self._lock:
            if target in self._memory["dependencies"]:
                if package_name not in self._memory["dependencies"][target]:
                    self._memory["dependencies"][target].append(package_name)

    def record_decision(self, agent_name: str, decision: str) -> None:
        with self._lock:
            self._memory["agent_decisions"].append({
                "agent": agent_name,
                "decision": decision
            })

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._memory)


global_project_memory_store = ProjectMemoryStore()
