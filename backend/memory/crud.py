from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.memory.database import ConversationDatabase
from backend.memory.models import ConversationRecord, MessageRecord


DEFAULT_CONVERSATION_TITLE = "Untitled Conversation"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_conversation_title(prompt: str) -> str:
    cleaned = (prompt or "").strip()
    cleaned = re.sub(r"^[\W_]+", "", cleaned)
    cleaned = re.sub(
        r"^(please\s+)?(help\s+me\s+)?(build|create|make|develop|design|start|write|generate|draft|compose|plan)\s+(a|an|the)?\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"^(i\s+want\s+to\s+|can\s+you\s+|could\s+you\s+|let'?s\s+)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,!?:;-")

    if not cleaned:
        return DEFAULT_CONVERSATION_TITLE

    words = cleaned.split()
    title = " ".join(words[:5]).title()
    return title or DEFAULT_CONVERSATION_TITLE


class ConversationRepository:

    def __init__(self, database: ConversationDatabase | None = None):
        self.database = database or ConversationDatabase()

    def _conversation_from_row(self, row) -> ConversationRecord:
        return ConversationRecord(
            conversation_id=row["conversation_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_opened_at=row["last_opened_at"],
            message_count=row["message_count"],
        )

    def _message_from_row(self, row) -> MessageRecord:
        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                metadata = {}

        return MessageRecord(
            message_id=row["message_id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            timestamp=row["timestamp"],
            metadata=metadata,
        )

    def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

        if row is None:
            return None

        return self._conversation_from_row(row)

    def create_conversation(
        self,
        conversation_id: str | None = None,
        title: str | None = None,
        created_at: str | None = None,
    ) -> ConversationRecord:
        now = created_at or _utc_now()
        conversation_id = conversation_id or uuid4().hex
        clean_title = (title or DEFAULT_CONVERSATION_TITLE).strip() or DEFAULT_CONVERSATION_TITLE

        with self.database.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

            if existing is None:
                connection.execute(
                    """
                    INSERT INTO conversations (
                        conversation_id, title, created_at, updated_at, last_opened_at, message_count
                    ) VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (conversation_id, clean_title, now, now, now),
                )
            elif title and existing["title"] != clean_title:
                connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?, updated_at = ?, last_opened_at = ?
                    WHERE conversation_id = ?
                    """,
                    (clean_title, now, now, conversation_id),
                )

            row = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

        return self._conversation_from_row(row)

    def ensure_conversation(self, conversation_id: str, title: str | None = None) -> ConversationRecord:
        conversation = self.get_conversation(conversation_id)
        if conversation is not None:
            if title and conversation.title != title:
                return self.rename_conversation(conversation_id, title)
            return conversation

        return self.create_conversation(conversation_id=conversation_id, title=title)

    def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
    ) -> list[ConversationRecord]:
        query = "SELECT * FROM conversations"
        params: list[Any] = []

        if search:
            query += " WHERE title LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY last_opened_at DESC, updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.database.connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._conversation_from_row(row) for row in rows]

    def rename_conversation(self, conversation_id: str, title: str) -> ConversationRecord:
        clean_title = (title or "").strip() or DEFAULT_CONVERSATION_TITLE
        now = _utc_now()

        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?, last_opened_at = ?
                WHERE conversation_id = ?
                """,
                (clean_title, now, now, conversation_id),
            )
            row = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

        if row is None:
            raise KeyError(conversation_id)

        return self._conversation_from_row(row)

    def delete_conversation(self, conversation_id: str) -> None:
        with self.database.connection() as connection:
            connection.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )

    def touch_conversation(self, conversation_id: str) -> ConversationRecord:
        now = _utc_now()
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?, last_opened_at = ?
                WHERE conversation_id = ?
                """,
                (now, now, conversation_id),
            )
            row = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

        if row is None:
            raise KeyError(conversation_id)

        return self._conversation_from_row(row)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> MessageRecord:
        if not content.strip():
            raise ValueError("Message content cannot be empty.")

        message_timestamp = timestamp or _utc_now()
        message_id = uuid4().hex
        metadata_text = json.dumps(metadata or {}, ensure_ascii=False)

        with self.database.connection() as connection:
            conversation = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if conversation is None:
                conversation_title = generate_conversation_title(content) if role == "user" else DEFAULT_CONVERSATION_TITLE
                connection.execute(
                    """
                    INSERT INTO conversations (
                        conversation_id, title, created_at, updated_at, last_opened_at, message_count
                    ) VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (conversation_id, conversation_title, message_timestamp, message_timestamp, message_timestamp),
                )
                conversation = connection.execute(
                    "SELECT * FROM conversations WHERE conversation_id = ?",
                    (conversation_id,),
                ).fetchone()

            previous_count = int(conversation["message_count"])

            connection.execute(
                """
                INSERT INTO messages (
                    message_id, conversation_id, role, content, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, conversation_id, role, content, message_timestamp, metadata_text),
            )

            title = conversation["title"]
            should_auto_title = (
                role == "user"
                and previous_count == 0
                and title in {DEFAULT_CONVERSATION_TITLE, "", "New Conversation", "Draft Conversation"}
            )

            if should_auto_title:
                auto_title = generate_conversation_title(content)
                connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?, updated_at = ?, last_opened_at = ?, message_count = message_count + 1
                    WHERE conversation_id = ?
                    """,
                    (auto_title, message_timestamp, message_timestamp, conversation_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?, last_opened_at = ?, message_count = message_count + 1
                    WHERE conversation_id = ?
                    """,
                    (message_timestamp, message_timestamp, conversation_id),
                )

            row = connection.execute(
                "SELECT * FROM messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()

        return self._message_from_row(row)

    def get_messages(
        self,
        conversation_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[MessageRecord]:
        query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC, message_id ASC"
        params: list[Any] = [conversation_id]

        if limit is not None and limit > 0:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        with self.database.connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._message_from_row(row) for row in rows]

    def get_last_message(self, conversation_id: str) -> MessageRecord | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp DESC, message_id DESC
                LIMIT 1
                """,
                (conversation_id,),
            ).fetchone()

        if row is None:
            return None

        return self._message_from_row(row)
