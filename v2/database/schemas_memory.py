"""
AIForge V2 – Persistent Memory Pydantic Schemas
================================================
Schemas for Projects, Tasks, Conversations, and Agent Telemetry.
"""

import time
from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectResponseSchema(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str = "active"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class TaskCreateSchema(BaseModel):
    project_id: str
    agent: str
    prompt: str
    result: Optional[str] = None
    execution_time: float = 0.0


class TaskResponseSchema(BaseModel):
    id: str
    project_id: str
    agent: str
    prompt: str
    result: Optional[str] = None
    status: str = "completed"
    execution_time: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class ConversationCreateSchema(BaseModel):
    project_id: str
    role: str
    message: str


class ConversationResponseSchema(BaseModel):
    id: str
    project_id: str
    role: str
    message: str
    created_at: float = Field(default_factory=time.time)


class AgentLogCreateSchema(BaseModel):
    project_id: Optional[str] = None
    agent: str
    input: Optional[str] = None
    output: Optional[str] = None
    duration: float = 0.0
    success: bool = True


class AgentLogResponseSchema(BaseModel):
    id: str
    project_id: Optional[str] = None
    agent: str
    input: Optional[str] = None
    output: Optional[str] = None
    duration: float = 0.0
    success: bool = True
    timestamp: float = Field(default_factory=time.time)
