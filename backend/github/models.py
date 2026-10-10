"""
AIForge Day 30 — GitHub Data Models
===================================
Models for Repository Connections, Branches, Commits, Pull Requests, CI Statuses, AI PR Reviews,
Change Plans, and Pre-Commit Secret Scans.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReviewDecisionEnum(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


class CIStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class RepositoryConnection(BaseModel):
    id: str
    project_id: str = "aiforge-demo"
    repo_name: str
    owner: str
    default_branch: str = "main"
    token_scrubbed: str = "[REDACTED_SECRET]"
    status: str = "CONNECTED"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class BranchInfo(BaseModel):
    name: str
    commit_sha: str
    is_protected: bool = False
    project_id: str = "aiforge-demo"


class CommitInfo(BaseModel):
    sha: str
    message: str
    author: str = "AIForge Agent <agent@aiforge.dev>"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    files_changed: List[str] = Field(default_factory=list)


class ChangePlan(BaseModel):
    problem: str
    evidence: str
    files: List[str]
    risk: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    tests_affected: int = 0


class SecretScanResult(BaseModel):
    contains_secrets: bool = False
    secrets_found: List[str] = Field(default_factory=list)
    blocked_commit: bool = False


class PullRequest(BaseModel):
    id: str
    number: int
    project_id: str = "aiforge-demo"
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"
    state: str = "open"  # open, closed, merged
    html_url: str = "https://github.com/SHASHANK8412/CodeForge-AI/pull/1"
    ci_status: CIStatusEnum = CIStatusEnum.SUCCESS
    review_status: ReviewDecisionEnum = ReviewDecisionEnum.APPROVE
    test_summary: str = "52/52 PASS"
    security_summary: str = "PASS"
    browser_summary: str = "24/24 PASS"
    performance_summary: str = "P95 improved"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class CIStatus(BaseModel):
    workflow_name: str = "Build & Test"
    status: CIStatusEnum = CIStatusEnum.SUCCESS
    run_number: int = 1
    attempts_count: int = 1
    error_log: Optional[str] = None


class ReviewResult(BaseModel):
    decision: ReviewDecisionEnum = ReviewDecisionEnum.APPROVE
    correctness: str = "PASS"
    security: str = "PASS"
    architecture: str = "PASS"
    maintainability: str = "PASS"
    feedback: str = "All automated checks and security gates passed."
