"""
AIForge Day 25 — AI Software Architect Simulator Pydantic Data Models
=======================================================================
Models for Architecture Nodes, Edges, Diagrams, Scenarios, Options, Impact Assessments,
Comparison Matrices, Failure Propagation Reports, ADR Records, Architecture Versions, and Scorecards.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ArchitectureNodeType(str, Enum):
    FRONTEND = "FRONTEND"
    API_GATEWAY = "API_GATEWAY"
    BACKEND_SERVICE = "BACKEND_SERVICE"
    DATABASE = "DATABASE"
    CACHE = "CACHE"
    MESSAGE_QUEUE = "MESSAGE_QUEUE"
    STORAGE = "STORAGE"
    EXTERNAL_API = "EXTERNAL_API"
    OBSERVABILITY = "OBSERVABILITY"


class EvidenceType(str, Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"


class ArchitectureNode(BaseModel):
    id: str
    label: str
    type: ArchitectureNodeType = ArchitectureNodeType.BACKEND_SERVICE
    technology: str = "FastAPI"
    status: str = "ACTIVE"
    spof_risk: str = "LOW"  # LOW, MEDIUM, HIGH


class ArchitectureEdge(BaseModel):
    source: str
    target: str
    protocol: str = "HTTP/REST"
    dependency_type: str = "SYNC"  # SYNC, ASYNC


class ArchitectureDiagram(BaseModel):
    project_id: str
    version: int = 1
    nodes: List[ArchitectureNode] = Field(default_factory=list)
    edges: List[ArchitectureEdge] = Field(default_factory=list)


class ArchitectureScenario(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    changes: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    status: str = "SIMULATION_ONLY"
    created_at: str = ""


class ImpactAssessment(BaseModel):
    scenario_id: str
    option_name: str
    performance_impact: str = "ESTIMATED_IMPROVEMENT"
    scalability_impact: str = "HIGH"
    security_impact: str = "MEDIUM_RISK"
    reliability_impact: str = "HIGH"
    complexity_impact: str = "INCREASED"
    maintenance_impact: str = "MODERATE"
    deployment_impact: str = "ADDITIONAL_INFRASTRUCTURE"
    testing_impact: str = "CACHE_INVALIDATION_TESTS"
    evidence_type: EvidenceType = EvidenceType.ESTIMATED
    confidence: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    affected_components_count: int = 0


class SimulatorScorecard(BaseModel):
    option_name: str
    performance_score: float = 8.5
    security_score: float = 7.5
    scalability_score: float = 9.0
    complexity_score: float = 6.0
    maintainability_score: float = 7.0
    cost_score: float = 7.0
    overall_score: float = 7.4


class ComparisonMatrix(BaseModel):
    scenario_id: str
    current_option: SimulatorScorecard
    proposed_options: List[SimulatorScorecard] = Field(default_factory=list)
    recommendation: str = ""
    rationale: str = ""


class FailurePropagationReport(BaseModel):
    failed_component: str
    project_id: str
    impact_level: str = "HIGH"
    affected_components: List[str] = Field(default_factory=list)
    affected_apis: List[str] = Field(default_factory=list)
    single_point_of_failure: bool = True
    mitigation_recommendation: str = ""


class ADRRecord(BaseModel):
    adr_id: str
    project_id: str
    title: str
    status: str = "APPROVED"  # APPROVED, REJECTED, PROPOSED
    decision: str = ""
    reason: str = ""
    alternatives_considered: List[str] = Field(default_factory=list)
    rejected_reasons: Dict[str, str] = Field(default_factory=dict)
    created_at: str = ""


class ArchitectureVersion(BaseModel):
    version: int
    project_id: str
    title: str
    diagram: ArchitectureDiagram
    adr_id: Optional[str] = None
    timestamp: str = ""
