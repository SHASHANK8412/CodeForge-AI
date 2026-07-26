import time
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger("aiforge.memory.history")


class HistoryEntry(BaseModel):
    session_id: str
    agent: str
    user_prompt: str
    llm_response: str
    execution_time: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class HistoryManager:
    """
    HistoryManager logs and tracks all user prompts, agent LLM responses, execution durations,
    and timestamps for debugging, rollback, analytics, and session history tracking.
    """

    def __init__(self):
        self._history: Dict[str, List[HistoryEntry]] = {}

    def add_history_entry(
        self,
        session_id: str,
        agent: str,
        user_prompt: str,
        llm_response: str,
        execution_time: float = 0.0
    ) -> HistoryEntry:
        """Appends a new history log entry for a given session."""
        entry = HistoryEntry(
            session_id=session_id,
            agent=agent,
            user_prompt=user_prompt,
            llm_response=llm_response,
            execution_time=execution_time,
            timestamp=time.time()
        )
        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].append(entry)
        logger.info(f"Added history entry for agent '{agent}' in session '{session_id}'")
        return entry

    def get_history(self, session_id: str) -> List[HistoryEntry]:
        """Retrieves history entries for a given session."""
        return self._history.get(session_id, [])

    def clear_history(self, session_id: str) -> bool:
        """Clears execution history for a given session."""
        if session_id in self._history:
            del self._history[session_id]
            return True
        return False
