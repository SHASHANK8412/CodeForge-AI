from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.config import CONVERSATION_HISTORY_TURNS
from backend.memory.context_store import ContextStore
from backend.memory.session_manager import SessionManager, ProjectSession
from backend.memory.history import HistoryManager, HistoryEntry

logger = logging.getLogger("aiforge.memory.memory_manager")


class MemoryManager:
    """
    Centralized Memory Manager for AIForge V2:
    - ContextStore: Structured agent stage outputs (planner, architect, frontend, backend, database, reviewer, testing, documentation).
    - SessionManager: Multi-project session state, generated file registries, and current step tracking.
    - HistoryManager: Chronological log of prompts, agent responses, execution times, and timestamps.
    """

    def __init__(self):
        self.context_store = ContextStore()
        self.session_manager = SessionManager()
        self.history_manager = HistoryManager()

    # --- Agent Output Operations ---

    def save_agent_output(self, session_id: str, agent_name: str, output: Any) -> None:
        """Stores or updates an agent's structured output in context store & updates session."""
        self.context_store.set_agent_output(agent_name, output)
        session = self.session_manager.get_or_create_session(session_id)
        session.current_step = agent_name

        # If output contains generated file strings or dicts, update session generated_files map
        if isinstance(output, str) and len(output) > 20:
            filename = f"{agent_name}_output.code"
            session.generated_files[filename] = output
        elif isinstance(output, dict):
            for k, v in output.items():
                if isinstance(v, str) and (k.endswith((".py", ".jsx", ".js", ".sql", ".md")) or "/" in k):
                    session.generated_files[k] = v

        self.session_manager.update_session(session_id, current_step=agent_name)
        logger.info(f"Memory saved for agent '{agent_name}' in session '{session_id}'")

    def get_agent_output(self, session_id: str, agent_name: str) -> Any:
        """Retrieves an agent's stored output."""
        return self.context_store.get_agent_output(agent_name)

    def update_agent_output(self, session_id: str, agent_name: str, output: Any) -> None:
        """Updates or merges an agent's output in context store."""
        self.context_store.update_agent_output(agent_name, output)
        logger.info(f"Memory updated for agent '{agent_name}' in session '{session_id}'")

    def delete_agent_output(self, session_id: str, agent_name: str) -> bool:
        """Deletes an agent's output from context store."""
        return self.context_store.delete_agent_output(agent_name)

    # --- Complete Project Memory & Context ---

    def get_project_memory(self, session_id: str) -> Dict[str, Any]:
        """Returns complete project memory including context store, session info, and history."""
        session = self.session_manager.get_session(session_id)
        context = self.context_store.get_context()
        history = [h.dict() for h in self.history_manager.get_history(session_id)]

        return {
            "session_id": session_id,
            "project_name": session.project_name if session else "Untitled Project",
            "current_step": session.current_step if session else "none",
            "context": context,
            "generated_files": session.generated_files if session else {},
            "history": history,
            "shared_stack": self.context_store.extract_shared_stack()
        }

    # --- Duplicate Generation Prevention ---

    def is_file_generated(self, session_id: str, filename: str) -> bool:
        """Checks if a file has already been generated in this session."""
        session = self.session_manager.get_session(session_id)
        if session and filename in session.generated_files:
            return True
        return False

    def get_existing_files(self, session_id: str) -> Dict[str, str]:
        """Returns all previously generated files for this session to prevent duplicate creation."""
        session = self.session_manager.get_session(session_id)
        if session:
            return session.generated_files
        return {}

    # --- Session & History Helpers ---

    def create_session(self, session_id: str, project_name: str = "Untitled Project") -> ProjectSession:
        return self.session_manager.create_session(session_id, project_name)

    def get_session(self, session_id: str) -> Optional[ProjectSession]:
        return self.session_manager.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        self.context_store.clear_context()
        self.history_manager.clear_history(session_id)
        return self.session_manager.delete_session(session_id)

    def add_history(self, session_id: str, agent: str, user_prompt: str, llm_response: str, execution_time: float = 0.0):
        return self.history_manager.add_history_entry(session_id, agent, user_prompt, llm_response, execution_time)

    def get_history(self, session_id: str) -> List[HistoryEntry]:
        return self.history_manager.get_history(session_id)


# Global Memory Manager Instance
memory_manager = MemoryManager()
