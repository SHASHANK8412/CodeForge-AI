"""
AIForge V2 – Inter-Agent Envelope Message Protocol
===================================================
Standard envelope message wrapper for agent-to-agent communication:
Sender, Receiver, Timestamp, Task ID, Payload, Metadata.
"""

import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CoreAgentMessage(BaseModel):
    message_id: str
    sender: str
    receiver: str
    task_id: Optional[str] = None
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
