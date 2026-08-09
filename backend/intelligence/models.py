"""
AIForge V2 — Extraordinary Features Pydantic Models
===================================================
Data models for What-If Engineering Simulator, Project Intelligence DNA Graph,
Adversarial Security Hunter (Bug Bounty), Multi-Agent Debate Arena,
Talk to Your Software Assistant, and Autonomous Production Readiness CTO Gate.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# --- What-If Engineering Simulator ---
class SimulationRequest(BaseModel):
    project_id: str
    proposed_change: str = Field(..., example="What happens if I switch PostgreSQL to MongoDB?")


class SimulationResult(BaseModel):
    simulation_id: str
    project_id: str
    proposed_change: str
    files_affected: int
    apis_affected: int
    tests_affected: int
    estimated_work_hours: float
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    recommendation: str = Field(..., description="ACCEPT or REJECT")
    reason: str
    affected_components: List[Dict[str, Any]] = Field(default_factory=list)


# --- AI Engineering DNA Graph ---
class DnaNode(BaseModel):
    id: str
    label: str
    type: str  # requirement, feature, api, service, database, test, deployment
    file_path: Optional[str] = None
    status: str = "healthy"


class DnaEdge(BaseModel):
    source: str
    target: str
    relation: str  # implements, calls, queries, verifies, deploys


class DnaGraphData(BaseModel):
    project_id: str
    nodes: List[DnaNode]
    edges: List[DnaEdge]


class ImpactQueryRequest(BaseModel):
    project_id: str
    target_node_or_component: str


# --- Autonomous Bug Bounty ---
class BugVulnerability(BaseModel):
    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # AUTH, INJECTION, SECRET, XSS, UNHANDLED_ERR
    title: str
    description: str
    file: str
    line: Optional[int] = None
    repaired: bool = False
    retest_status: str = "PASS"


class SecurityReport(BaseModel):
    project_id: str
    vulnerabilities_investigated: int
    safe_count: int
    vulnerabilities_found: int
    vulnerabilities: List[BugVulnerability]
    status: str = "SECURE"


# --- Multi-Agent Debate Arena ---
class DebateProposal(BaseModel):
    architect_id: str  # Architect A, Architect B, Architect C
    architecture_name: str
    stack: Dict[str, str]
    pros: List[str]
    cons: List[str]
    score: float


class DebateVerdict(BaseModel):
    debate_id: str
    winning_architect: str
    selected_architecture: str
    reason: str
    proposals: List[DebateProposal]
    overall_score: float


# --- Talk to Your Software Assistant ---
class SoftwareAssistantQuery(BaseModel):
    project_id: str
    query: str


class SoftwareAssistantResponse(BaseModel):
    answer: str
    relevant_files: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


# --- Production Readiness Autonomous CTO Gate ---
class ReadinessDimension(BaseModel):
    name: str  # Security, Architecture, Testing, Performance, Database, Documentation
    score: float
    status: str  # PASS, WARN, FAIL
    blocking_issue: Optional[str] = None


class CtoGateReport(BaseModel):
    project_id: str
    overall_score: float
    decision: str  # APPROVED or BLOCKED
    blocking_issues: List[str] = Field(default_factory=list)
    dimensions: List[ReadinessDimension]
