import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aiforge.memory.session_manager")


class ProjectSession(BaseModel):
    session_id: str
    project_name: str = "Untitled Project"
    current_step: str = "initialized"
    generated_files: Dict[str, str] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionManager:
    """
    SessionManager handles concurrent project sessions, maintaining isolated memory,
    generated file maps, and progress steps for each project.
    """

    def __init__(self):
        self._sessions: Dict[str, ProjectSession] = {}

    def create_session(self, session_id: str, project_name: str = "Untitled Project") -> ProjectSession:
        """Creates and stores a new project session."""
        session = ProjectSession(
            session_id=session_id,
            project_name=project_name,
            created_at=time.time(),
            updated_at=time.time()
        )
        self._sessions[session_id] = session
        logger.info(f"Created session '{session_id}' for project '{project_name}'")
        return session

    def get_session(self, session_id: str) -> Optional[ProjectSession]:
        """Retrieves an existing project session."""
        return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str, project_name: str = "Untitled Project") -> ProjectSession:
        """Retrieves an existing session or creates a new one if it does not exist."""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id, project_name)
        return session

    def update_session(
        self,
        session_id: str,
        current_step: Optional[str] = None,
        generated_files: Optional[Dict[str, str]] = None,
        project_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ProjectSession]:
        """Updates properties of an active session."""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id, project_name or "Untitled Project")

        if current_step:
            session.current_step = current_step
        if generated_files:
            session.generated_files.update(generated_files)
        if project_name:
            session.project_name = project_name
        if metadata:
            session.metadata.update(metadata)

        session.updated_at = time.time()
        return session

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Returns a list of all active sessions and their summaries."""
        return [
            {
                "session_id": s.session_id,
                "project_name": s.project_name,
                "current_step": s.current_step,
                "file_count": len(s.generated_files),
                "created_at": s.created_at,
                "updated_at": s.updated_at
            }
            for s in self._sessions.values()
        ]

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session '{session_id}'")
            return True
        return False

    def clear_all(self) -> None:
        """Clears all sessions."""
        self._sessions.clear()


# Global SessionManager Instance
global_session_manager = SessionManager()
