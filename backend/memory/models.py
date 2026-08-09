from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    REQUIREMENT = "REQUIREMENT"
    ARCHITECTURE = "ARCHITECTURE"
    DECISION = "DECISION"
    TECHNOLOGY = "TECHNOLOGY"
    API = "API"
    DATABASE = "DATABASE"
    FILE = "FILE"
    REVIEW = "REVIEW"
    TEST = "TEST"
    ERROR = "ERROR"
    FIX = "FIX"
    USER_PREFERENCE = "USER_PREFERENCE"


class ImportanceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProjectMemory(BaseModel):
    """
    Persistent memory record associated with a user's project across generations.
    """
    id: str = Field(..., description="Unique memory ID, e.g., mem_123abc")
    project_id: str = Field(..., description="Target project identifier")
    generation_id: Optional[str] = Field(default=None, description="Generation session ID if applicable")
    user_id: Optional[str] = Field(default=None, description="Owner user ID")
    memory_type: MemoryType = Field(..., description="Category of memory item")
    key: str = Field(..., description="Lookup key or title")
    value: Any = Field(..., description="Stored memory content or payload")
    source_agent: str = Field(..., description="Agent or process that created this memory")
    importance: ImportanceLevel = Field(default=ImportanceLevel.MEDIUM, description="Retrieval priority")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 update timestamp")


class DecisionRecord(BaseModel):
    """
    Explicit architectural decision record explaining choices made by agents.
    """
    id: str = Field(..., description="Unique decision ID, e.g., dec_456def")
    project_id: str = Field(..., description="Target project identifier")
    generation_id: Optional[str] = Field(default=None, description="Generation session ID")
    decision: str = Field(..., description="Concise statement of the decision made")
    reason: str = Field(..., description="Technical justification or tradeoff rationale")
    agent: str = Field(..., description="Agent that made the decision")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    importance: ImportanceLevel = Field(default=ImportanceLevel.HIGH, description="Decision significance level")


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
