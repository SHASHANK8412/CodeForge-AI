"""
AIForge Day 22 — Long-Term Engineering Memory & Knowledge Graph Pydantic Data Models
====================================================================================
Models for Engineering Memories, Memory Types, Importance Levels, Confidence Levels,
Sources, Statuses, Relationships, Knowledge Graph Nodes/Edges, Contexts, Quality Scores,
and backward-compatible ProjectMemory / DecisionRecord models.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    # Day 12 Legacy Types
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

    # Day 22 Structured Memory Types
    ARCHITECTURE_DECISION = "ARCHITECTURE_DECISION"
    PROJECT_CONSTRAINT = "PROJECT_CONSTRAINT"
    CODING_PATTERN = "CODING_PATTERN"
    SECURITY_LESSON = "SECURITY_LESSON"
    PERFORMANCE_LESSON = "PERFORMANCE_LESSON"
    INCIDENT = "INCIDENT"
    INCIDENT_LESSON = "INCIDENT_LESSON"
    DEPLOYMENT_LESSON = "DEPLOYMENT_LESSON"
    TESTING_LESSON = "TESTING_LESSON"
    REPAIR_HISTORY = "REPAIR_HISTORY"
    FAILED_APPROACH = "FAILED_APPROACH"
    SUCCESSFUL_APPROACH = "SUCCESSFUL_APPROACH"
    TECHNOLOGY_DECISION = "TECHNOLOGY_DECISION"
    KNOWN_LIMITATION = "KNOWN_LIMITATION"


class MemoryImportance(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Alias for backward compatibility
ImportanceLevel = MemoryImportance


class MemoryConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MemorySource(str, Enum):
    USER = "USER"
    AGENT = "AGENT"
    RAG = "RAG"
    ENGINEERING_DNA = "ENGINEERING_DNA"
    SECURITY = "SECURITY"
    TESTING = "TESTING"
    PERFORMANCE = "PERFORMANCE"
    INCIDENT = "INCIDENT"
    DEPLOYMENT = "DEPLOYMENT"
    DEBATE = "DEBATE"
    REVIEWER = "REVIEWER"


class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"
    INVALID = "INVALID"


class RelationshipType(str, Enum):
    CAUSED = "CAUSED"
    RESOLVED_BY = "RESOLVED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    SUPERSEDES = "SUPERSEDES"
    CONTRADICTS = "CONTRADICTS"
    RELATED_TO = "RELATED_TO"
    DERIVED_FROM = "DERIVED_FROM"
    VALIDATES = "VALIDATES"
    INVALIDATES = "INVALIDATES"


class MemoryVisibility(str, Enum):
    USER_VISIBLE = "USER_VISIBLE"
    AGENT_ONLY = "AGENT_ONLY"
    SYSTEM = "SYSTEM"


class EngineeringMemory(BaseModel):
    id: str
    project_id: str
    type: MemoryType = MemoryType.ARCHITECTURE_DECISION
    title: str
    content: str
    importance: MemoryImportance = MemoryImportance.HIGH
    confidence: MemoryConfidence = MemoryConfidence.HIGH
    source: MemorySource = MemorySource.DEBATE
    visibility: MemoryVisibility = MemoryVisibility.USER_VISIBLE
    version: int = 1
    status: MemoryStatus = MemoryStatus.ACTIVE
    created_at: str = ""
    updated_at: str = ""
    last_used_at: Optional[str] = None
    usage_count: int = 0
    tags: List[str] = Field(default_factory=list)
    related_nodes: List[str] = Field(default_factory=list)  # DNA node IDs or component names
    related_memories: List[str] = Field(default_factory=list)  # Memory IDs
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryNode(BaseModel):
    id: str
    label: str
    type: str
    importance: str = "HIGH"
    status: str = "ACTIVE"


class MemoryEdge(BaseModel):
    source: str
    target: str
    relationship: RelationshipType = RelationshipType.RELATED_TO


class MemoryGraph(BaseModel):
    project_id: str
    nodes: List[MemoryNode] = Field(default_factory=list)
    edges: List[MemoryEdge] = Field(default_factory=list)


class MemoryContext(BaseModel):
    project_id: str
    task: str
    agent_type: str
    relevant_memories: List[EngineeringMemory] = Field(default_factory=list)


class MemoryQualityScore(BaseModel):
    total_memories: int = 0
    active_count: int = 0
    superseded_count: int = 0
    archived_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    duplicate_rate: float = 0.0
    contradiction_rate: float = 0.0


# Backward-compatible models for Day 12 Project Memory
class ProjectMemory(BaseModel):
    id: str = Field(..., description="Unique memory ID")
    project_id: str = Field(..., description="Target project identifier")
    generation_id: Optional[str] = Field(default=None, description="Generation session ID")
    user_id: Optional[str] = Field(default=None, description="Owner user ID")
    memory_type: MemoryType = Field(..., description="Category of memory item")
    key: str = Field(..., description="Lookup key or title")
    value: Any = Field(..., description="Stored memory content")
    source_agent: str = Field(..., description="Agent that created memory")
    importance: ImportanceLevel = Field(default=ImportanceLevel.MEDIUM, description="Retrieval priority")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO update timestamp")


class DecisionRecord(BaseModel):
    id: str = Field(..., description="Unique decision ID")
    project_id: str = Field(..., description="Target project identifier")
    generation_id: Optional[str] = Field(default=None, description="Generation session ID")
    decision: str = Field(..., description="Statement of decision made")
    reason: str = Field(..., description="Technical justification")
    agent: str = Field(..., description="Agent that made decision")
    timestamp: str = Field(..., description="ISO timestamp")
    importance: ImportanceLevel = Field(default=ImportanceLevel.HIGH, description="Decision significance")


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
