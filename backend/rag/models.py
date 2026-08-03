"""
AIForge V2 — Day 13 Data Models
Strongly-typed schemas for Production RAG, Hybrid Retrieval, Grounding, Citations & Hallucination Control.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RetrievalDomain(str, Enum):
    REPOSITORY = "REPOSITORY"
    DOCUMENT = "DOCUMENT"
    MEMORY = "MEMORY"
    DOCUMENTATION = "DOCUMENTATION"
    PROJECT = "PROJECT"
    MIXED = "MIXED"


class QueryType(str, Enum):
    FACT_LOOKUP = "FACT_LOOKUP"
    CODE_SEARCH = "CODE_SEARCH"
    CONCEPT_SEARCH = "CONCEPT_SEARCH"
    MULTI_HOP = "MULTI_HOP"
    SUMMARY = "SUMMARY"
    COMPARISON = "COMPARISON"
    DEBUG_CONTEXT = "DEBUG_CONTEXT"
    IMPLEMENTATION_CONTEXT = "IMPLEMENTATION_CONTEXT"


class GroundingStatus(str, Enum):
    GROUNDED = "GROUNDED"
    PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SourceRecord(BaseModel):
    source_id: str
    source_type: str  # e.g., 'pdf', 'txt', 'md', 'docx', 'repository'
    name: str
    version: str = "1.0"
    content_hash: str
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    chunk_id: str
    source_id: str
    domain: RetrievalDomain
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str
    position: int = 0
    token_count: int = 0
    # Repository specific metadata
    repository_id: Optional[str] = None
    path: Optional[str] = None
    symbol: Optional[str] = None
    language: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    # Document specific metadata
    document_id: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    heading: Optional[str] = None


class RetrievalDecision(BaseModel):
    required: bool
    domains: List[RetrievalDomain] = Field(default_factory=list)
    reason: str
    query_type: QueryType
    rewritten_queries: List[str] = Field(default_factory=list)
    subqueries: List[str] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    target_symbols: List[str] = Field(default_factory=list)


class RetrievalCandidate(BaseModel):
    chunk_id: str
    source_id: str
    domain: RetrievalDomain
    score: float
    retrieval_method: str  # 'vector', 'keyword', 'symbol', 'structural', 'fast_path'
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GroundingContext(BaseModel):
    query: str
    sources: List[SourceRecord] = Field(default_factory=list)
    chunks: List[ChunkRecord] = Field(default_factory=list)
    coverage: float = 0.0
    confidence_category: str = "HIGH"
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    source_labels: Dict[str, str] = Field(default_factory=dict)  # chunk_id -> '[S1]'


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    display: str  # e.g., '[S1] backend/routes/auth.py:42-78' or '[S2] architecture.pdf (Page 7)'
    location: str  # file + lines or doc + page


class GroundedResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    grounding_status: GroundingStatus
    confidence_score: float = 1.0
    evidence_summary: str = ""


class GroundingValidation(BaseModel):
    supported_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    partially_supported: List[str] = Field(default_factory=list)
    grounding_score: float = 1.0
    status: GroundingStatus
    reason: str = ""
