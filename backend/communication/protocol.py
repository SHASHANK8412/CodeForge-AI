"""
AIForge Agent Communication Protocol
=====================================
Defines message schemas, message types, priorities, and data structures for inter-agent communication.
"""

import time
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MessageType:
    TASK = "TASK"
    RESPONSE = "RESPONSE"
    REQUEST = "REQUEST"
    ERROR = "ERROR"
    EVENT = "EVENT"
    WARNING = "WARNING"
    COMPLETE = "COMPLETE"

    ALL_TYPES = [TASK, RESPONSE, REQUEST, ERROR, EVENT, WARNING, COMPLETE]


class MessagePriority:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    ALL_PRIORITIES = [CRITICAL, HIGH, MEDIUM, LOW]


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{int(time.time() * 1000)}_{str(uuid.uuid4())[:4]}")
    sender: str
    receiver: str
    type: str  # MessageType
    priority: str = MessagePriority.MEDIUM
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = False
    processed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "acknowledged": self.acknowledged,
            "processed": self.processed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(**data)
