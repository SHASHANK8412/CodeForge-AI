from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.memory.conversation_manager import ConversationManager
from backend.memory.crud import ConversationRepository
from backend.memory.database import ConversationDatabase


class ConversationMemory:

    def __init__(self, storage_root: Path | None = None):
        self.storage_root = storage_root or Path(__file__).resolve().parent / "store"
        self._manager: ConversationManager | None = None
        self._manager_path: Path | None = None

    def _database_path(self) -> Path:
        if self.storage_root.suffix.lower() == ".db":
            return self.storage_root
        return self.storage_root / "conversation_memory.db"

    def _get_manager(self) -> ConversationManager:
        database_path = self._database_path()
        if self._manager is None or self._manager_path != database_path:
            database_path.parent.mkdir(parents=True, exist_ok=True)
            database = ConversationDatabase(database_path)
            repository = ConversationRepository(database)
            self._manager = ConversationManager(repository)
            self._manager_path = database_path
        return self._manager

    def save_message(
        self,
        session_id: str,
        user_prompt: str,
        ai_response: str,
        agent_name: str = "",
        route: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bundle = self._get_manager().record_turn(
            conversation_id=session_id,
            user_prompt=user_prompt,
            assistant_response=ai_response,
            metadata={
                **(metadata or {}),
                "agent_name": agent_name,
                "route": route,
            },
        )

        turns = self._get_manager().to_turns(bundle.messages)
        return turns[-1] if turns else {
            "session_id": session_id,
            "timestamp": "",
            "user_prompt": user_prompt,
            "ai_response": ai_response,
            "agent_name": agent_name,
            "route": route,
            "metadata": metadata or {},
        }

    def get_history(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        manager = self._get_manager()
        messages = manager.get_messages(session_id)
        turns = manager.to_turns(messages)

        if limit is not None and limit > 0:
            return turns[-limit:]

        return turns

    def clear_history(self, session_id: str) -> None:
        self._get_manager().delete_conversation(session_id)

    def last_message(self, session_id: str) -> dict[str, Any] | None:
        last_message = self._get_manager().get_last_message(session_id)
        if last_message is None:
            return None

        return {
            "session_id": last_message.conversation_id,
            "timestamp": last_message.timestamp,
            "role": last_message.role,
            "content": last_message.content,
            "metadata": last_message.metadata,
        }
