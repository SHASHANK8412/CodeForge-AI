from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.memory.crud import ConversationRepository, generate_conversation_title
from backend.memory.models import ConversationRecord, MessageRecord


@dataclass(slots=True)
class ConversationHistoryBundle:
    conversation: ConversationRecord
    messages: list[MessageRecord]


class ConversationManager:

    def __init__(self, repository: ConversationRepository | None = None):
        self.repository = repository or ConversationRepository()

    def create_conversation(self, conversation_id: str | None = None, title: str | None = None) -> ConversationRecord:
        return self.repository.create_conversation(conversation_id=conversation_id, title=title)

    def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        return self.repository.get_conversation(conversation_id)

    def list_conversations(self, limit: int = 50, offset: int = 0, search: str | None = None) -> list[ConversationRecord]:
        return self.repository.list_conversations(limit=limit, offset=offset, search=search)

    def rename_conversation(self, conversation_id: str, title: str) -> ConversationRecord:
        return self.repository.rename_conversation(conversation_id, title)

    def delete_conversation(self, conversation_id: str) -> None:
        self.repository.delete_conversation(conversation_id)

    def load_conversation(self, conversation_id: str) -> ConversationHistoryBundle:
        conversation = self.repository.get_conversation(conversation_id)
        if conversation is None:
            conversation = self.repository.create_conversation(conversation_id=conversation_id)

        messages = self.repository.get_messages(conversation_id)
        return ConversationHistoryBundle(conversation=conversation, messages=messages)

    def get_messages(self, conversation_id: str, limit: int | None = None) -> list[MessageRecord]:
        return self.repository.get_messages(conversation_id, limit=limit)

    def get_last_message(self, conversation_id: str) -> MessageRecord | None:
        return self.repository.get_last_message(conversation_id)

    def record_turn(
        self,
        conversation_id: str,
        user_prompt: str,
        assistant_response: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationHistoryBundle:
        if not user_prompt.strip():
            raise ValueError("User prompt cannot be empty.")

        conversation = self.repository.get_conversation(conversation_id)
        if conversation is None:
            conversation = self.repository.create_conversation(
                conversation_id=conversation_id,
                title=generate_conversation_title(user_prompt),
            )

        payload = metadata or {}
        self.repository.add_message(conversation_id, "user", user_prompt, metadata={**payload, "turn": "user"})
        self.repository.add_message(conversation_id, "assistant", assistant_response, metadata={**payload, "turn": "assistant"})

        updated_conversation = self.repository.touch_conversation(conversation_id)
        messages = self.repository.get_messages(conversation_id)
        return ConversationHistoryBundle(conversation=updated_conversation, messages=messages)

    def to_turns(self, messages: list[MessageRecord]) -> list[dict[str, Any]]:
        turns: list[dict[str, Any]] = []
        pending_user: MessageRecord | None = None

        for message in messages:
            if message.role == "user":
                pending_user = message
                continue

            if message.role == "assistant" and pending_user is not None:
                turn_metadata = {
                    **(pending_user.metadata or {}),
                    **(message.metadata or {}),
                }
                turns.append(
                    {
                        "session_id": pending_user.conversation_id,
                        "timestamp": message.timestamp,
                        "user_prompt": pending_user.content,
                        "ai_response": message.content,
                        "agent_name": turn_metadata.get("agent_name", ""),
                        "route": turn_metadata.get("route", ""),
                        "metadata": turn_metadata,
                        "messages": [
                            {
                                "message_id": pending_user.message_id,
                                "role": pending_user.role,
                                "content": pending_user.content,
                                "timestamp": pending_user.timestamp,
                                "metadata": pending_user.metadata,
                            },
                            {
                                "message_id": message.message_id,
                                "role": message.role,
                                "content": message.content,
                                "timestamp": message.timestamp,
                                "metadata": message.metadata,
                            },
                        ],
                    }
                )
                pending_user = None

        return turns
