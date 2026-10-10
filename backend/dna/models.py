"""
AIForge Day 15 — Engineering DNA Pydantic Data Models
=====================================================
Models for Graph Nodes, Edges, Normalized Graph, Impact Analysis,
Requirement Traceability, Dead Code, Circular Dependencies, Versioning, and Diffing.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class NodeKind(str, Enum):
    FILE = "FILE"
    FUNCTION = "FUNCTION"
    CLASS = "CLASS"
    COMPONENT = "COMPONENT"
    API = "API"
    DATABASE_MODEL = "DATABASE_MODEL"
    DATABASE_TABLE = "DATABASE_TABLE"
    TEST = "TEST"
    REQUIREMENT = "REQUIREMENT"
    FEATURE = "FEATURE"
    CONFIGURATION = "CONFIGURATION"


class RelationType(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    RENDERS = "RENDERS"
    USES = "USES"
    EXPOSES = "EXPOSES"
    DEPENDS_ON = "DEPENDS_ON"
    STORES_IN = "STORES_IN"
    TESTS = "TESTS"
    IMPLEMENTS = "IMPLEMENTS"
    REQUIRES = "REQUIRES"


class GraphNode(BaseModel):
    id: str
    label: str
    kind: NodeKind
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    security_critical: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: RelationType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EngineeringDNAGraph(BaseModel):
    project_id: str
    version: int = 1
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    created_at: str = ""


class ImpactAnalysisResult(BaseModel):
    node_id: str
    change_type: str = "modify"  # modify, remove, refactor
    affected_files: List[str] = Field(default_factory=list)
    affected_components: List[str] = Field(default_factory=list)
    affected_apis: List[str] = Field(default_factory=list)
    affected_database_objects: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    affected_features: List[str] = Field(default_factory=list)
    security_impact: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float = 0.95
    recommendation: str = "Safe to apply change"
    explanation: str = ""


class RequirementTraceResult(BaseModel):
    requirement_id: str
    text: str
    status: str = "IMPLEMENTED"  # IMPLEMENTED, UNIMPLEMENTED, PARTIAL
    feature: Optional[str] = None
    components: List[str] = Field(default_factory=list)
    apis: List[str] = Field(default_factory=list)
    database_tables: List[str] = Field(default_factory=list)
    tests: List[str] = Field(default_factory=list)
    coverage_percent: float = 100.0


class DeadCodeFinding(BaseModel):
    node_id: str
    kind: NodeKind
    file_path: str
    name: str
    reason: str = "No incoming dependencies detected"


class CircularDependencyFinding(BaseModel):
    cycle: List[str] = Field(default_factory=list)
    severity: str = "HIGH"
    recommendation: str = "Refactor shared dependency into a separate utility module."


class GraphDiffResult(BaseModel):
    old_version: int
    new_version: int
    added_nodes: List[GraphNode] = Field(default_factory=list)
    removed_nodes: List[GraphNode] = Field(default_factory=list)
    added_edges: List[GraphEdge] = Field(default_factory=list)
    removed_edges: List[GraphEdge] = Field(default_factory=list)
    risk_assessment: str = "LOW"
