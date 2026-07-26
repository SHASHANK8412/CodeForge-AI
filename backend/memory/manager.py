import logging
from typing import Dict, Any, List, Optional

from backend.memory.short_term import ShortTermMemory, global_short_term_memory
from backend.memory.long_term import LongTermMemory, global_long_term_memory
from backend.memory.versioning import VersionControlManager, global_version_manager
from backend.memory.context_builder import ContextBuilder, global_context_builder
from backend.memory.history import HistoryManager, HistoryEntry

logger = logging.getLogger("aiforge.memory.manager")


class CentralMemoryManager:
    """
    CentralMemoryManager provides a unified interface over short-term memory,
    long-term persistent project storage, version control management, and context building.
    """

    def __init__(self):
        self.short_term = global_short_term_memory
        self.long_term = global_long_term_memory
        self.version_control = global_version_manager
        self.context_builder = global_context_builder
        self.history_manager = HistoryManager()

    def save_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves project to long-term memory and creates a version snapshot."""
        record = self.long_term.save_project(project_id, data)
        self.version_control.create_version(
            project_id=project_id,
            commit_message=data.get("commit_message", "Automated AIForge Build"),
            files=record.get("generated_files", {}),
            architecture=record.get("architecture", {})
        )
        return record

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.long_term.get_project(project_id)

    def list_projects(self) -> List[Dict[str, Any]]:
        return self.long_term.list_projects()

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.long_term.update_project(project_id, updates)

    def delete_project(self, project_id: str) -> bool:
        return self.long_term.delete_project(project_id)

    def search_projects(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.long_term.search_semantic(query, top_k=top_k)

    def resume_project(self, project_id: str, new_prompt: str) -> Dict[str, Any]:
        """Resumes an existing project by loading its long-term memory and creating a new version v2/v3."""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found in long-term memory.")

        # Increment version
        current_ver = project.get("version", "v1")
        ver_num = int(current_ver.replace("v", "")) + 1
        new_version = f"v{ver_num}"

        project["version"] = new_version
        project["prompt"] = f"{project.get('prompt', '')}\nFollow-up: {new_prompt}"
        self.long_term.save_project(project_id, project)

        self.version_control.create_version(
            project_id=project_id,
            commit_message=f"Resumed project: {new_prompt[:40]}",
            files=project.get("generated_files", {}),
            architecture=project.get("architecture", {})
        )

        logger.info(f"Resumed project '{project_id}' to version '{new_version}'")
        return project


# Global CentralMemoryManager instance
central_memory_manager = CentralMemoryManager()
