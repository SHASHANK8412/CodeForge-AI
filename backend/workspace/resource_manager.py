"""
AIForge Resource Allocation Manager
===================================
Manages system and AI resource allocations across projects including LLM model selection, CPU/memory limits, plugin access, and execution queue concurrency.
"""

from typing import Dict, Any, List, Optional


class ResourceManager:
    """
    Allocates and monitors computational and LLM resources per project.
    """

    def __init__(self) -> None:
        self.default_allocation: Dict[str, Any] = {
            "llm_model": "gpt-4o",
            "fallback_model": "gpt-3.5-turbo",
            "max_tokens_per_min": 100000,
            "cpu_limit": "2.0 Cores",
            "memory_limit": "4.0 GB",
            "max_concurrent_agents": 3,
            "enabled_plugins": ["git_integration", "docker_runner", "pytest_validator", "security_scanner"],
            "execution_queue_capacity": 10
        }

        self.project_allocations: Dict[str, Dict[str, Any]] = {}

    def get_resource_allocation(self, project_id: str) -> Dict[str, Any]:
        if project_id in self.project_allocations:
            return self.project_allocations[project_id]
        
        # Return default allocation tailored to project_id
        alloc = dict(self.default_allocation)
        alloc["project_id"] = project_id
        return alloc

    def update_resource_allocation(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_resource_allocation(project_id)
        current.update(updates)
        current["project_id"] = project_id
        self.project_allocations[project_id] = current
        return current

    def get_all_resource_allocations(self) -> List[Dict[str, Any]]:
        return list(self.project_allocations.values()) if self.project_allocations else [
            self.get_resource_allocation("proj_ecommerce"),
            self.get_resource_allocation("proj_hospital"),
            self.get_resource_allocation("proj_airesume"),
            self.get_resource_allocation("proj_crm")
        ]


global_resource_manager = ResourceManager()
