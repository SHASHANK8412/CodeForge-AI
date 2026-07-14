from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ConversationRecord:
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    last_opened_at: str
    message_count: int = 0


@dataclass(slots=True)
class MessageRecord:
    message_id: str
    conversation_id: str
    role: str
    content: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
