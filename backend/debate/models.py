"""
AIForge Day 16 — Multi-Agent Architecture Debate Pydantic Models
==================================================================
Models for Architecture Proposals, Evidence Claims, Judge Scores,
Judge Decisions, Architecture Decision Records (ADRs), and Debate Sessions.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DebateThreshold(str, Enum):
    LOW = "LOW"            # Normal Architect
    MEDIUM = "MEDIUM"      # 2 Candidates
    HIGH = "HIGH"          # 3 Candidates + Judge
    CRITICAL = "CRITICAL"  # 3 Candidates + Judge + Security Review


class EvidenceItem(BaseModel):
    source: str  # project_memory, engineering_dna, rag, requirements, security
    claim: str
    relevance: float = 0.95


class ArchitectureProposal(BaseModel):
    candidate_id: str  # A, B, C
    name: str  # e.g., "PostgreSQL + REST + Redis"
    architecture: str
    technology_stack: List[str] = Field(default_factory=list)
    advantages: List[str] = Field(default_factory=list)
    disadvantages: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    estimated_complexity: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    requirements_supported: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)


class JudgeScoreBreakdown(BaseModel):
    candidate_id: str
    requirements_fit: float
    scalability: float
    security: float
    maintainability: float
    performance: float
    complexity: float
    cost: float
    aiforge_fit: float
    total_weighted_score: float


class ADRecord(BaseModel):
    adr_id: str  # e.g. ADR-007
    title: str
    decision: str
    context: str
    alternatives: List[str] = Field(default_factory=list)
    selected_option: str
    tradeoffs: List[str] = Field(default_factory=list)
    status: str = "ACCEPTED"  # ACCEPTED, REJECTED, PENDING_APPROVAL
    timestamp: str = ""


class JudgeDecision(BaseModel):
    winner: str  # Candidate ID e.g., "B"
    winning_proposal_name: str
    scores: Dict[str, JudgeScoreBreakdown] = Field(default_factory=dict)
    reason: str
    tradeoffs: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    confidence: float = 0.95
    requires_human_approval: bool = False
    disagreement_summary: Optional[str] = None
    minority_report: Optional[str] = None
    adr: Optional[ADRecord] = None


class DebateSession(BaseModel):
    debate_id: str
    project_id: str
    generation_id: str = "aiforge-demo"
    requirement: str
    threshold: DebateThreshold = DebateThreshold.HIGH
    candidates: List[ArchitectureProposal] = Field(default_factory=list)
    decision: Optional[JudgeDecision] = None
    status: str = "COMPLETED"  # RUNNING, COMPLETED, PENDING_APPROVAL, REJECTED
    created_at: str = ""
