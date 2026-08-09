"""
AIForge Day 12 - Git Workflow & Engineering Models
===================================================
Typed data structures for Issue-to-Code workflow, Git management,
Worktrees, Diff Analysis, Review, Commit Preparation, and PR Drafts.
"""

import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class EngineeringTaskSource(str, Enum):
    USER_PROMPT = "USER_PROMPT"
    ISSUE = "ISSUE"
    LOCAL_TASK = "LOCAL_TASK"
    PROJECT_WORKFLOW = "PROJECT_WORKFLOW"


class TaskRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkflowStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    ANALYZING = "ANALYZING"
    PLANNED = "PLANNED"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    REVIEWING = "REVIEWING"
    READY_FOR_COMMIT = "READY_FOR_COMMIT"
    COMMITTED = "COMMITTED"
    READY_FOR_PR = "READY_FOR_PR"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class GitWorkflowMode(str, Enum):
    PREPARE_ONLY = "PREPARE_ONLY"
    LOCAL_ONLY = "LOCAL_ONLY"
    REMOTE_PR = "REMOTE_PR"


class VerificationLevel(str, Enum):
    NONE = "NONE"
    TARGETED = "TARGETED"
    AFFECTED = "AFFECTED"
    FULL = "FULL"
    CI_VERIFIED = "CI_VERIFIED"


class RemoteActionType(str, Enum):
    FETCH = "FETCH"
    PUSH = "PUSH"
    CREATE_PR = "CREATE_PR"
    UPDATE_PR = "UPDATE_PR"
    MERGE_PR = "MERGE_PR"
    FORCE_PUSH = "FORCE_PUSH"
    DELETE_REMOTE_BRANCH = "DELETE_REMOTE_BRANCH"
    CLOSE_ISSUE = "CLOSE_ISSUE"
    COMMENT_ISSUE = "COMMENT_ISSUE"


@dataclass
class EngineeringTask:
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    source: EngineeringTaskSource = EngineeringTaskSource.USER_PROMPT
    title: str = ""
    description: str = ""
    repository_id: str = "default_repo"
    base_ref: str = "main"
    task_type: str = "feature"  # feature, bugfix, refactor, docs
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IssueContext:
    provider: str = "github"
    issue_id: str = ""
    title: str = ""
    body: str = ""
    labels: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IssueAnalysis:
    summary: str = ""
    task_type: str = "feature"
    requirements: List[str] = field(default_factory=list)
    acceptance_criteria: List[Dict[str, str]] = field(default_factory=list)  # {"given": "", "when": "", "then": ""}
    keywords: List[str] = field(default_factory=list)
    likely_components: List[str] = field(default_factory=list)
    risk: TaskRisk = TaskRisk.LOW
    ambiguities: List[str] = field(default_factory=list)
    is_ambiguous: bool = False


@dataclass
class WorkflowTestEvidence:
    baseline: List[Dict[str, Any]] = field(default_factory=list)
    targeted: List[Dict[str, Any]] = field(default_factory=list)
    affected: List[Dict[str, Any]] = field(default_factory=list)
    full: List[Dict[str, Any]] = field(default_factory=list)
    new_failures: List[str] = field(default_factory=list)
    pre_existing_failures: List[str] = field(default_factory=list)
    verification_status: VerificationLevel = VerificationLevel.NONE


@dataclass
class DiffAnalysis:
    files_changed: List[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    unexpected_files: List[str] = field(default_factory=list)
    sensitive_changes: List[str] = field(default_factory=list)
    risk: TaskRisk = TaskRisk.LOW
    summary: str = ""
    has_secrets: bool = False
    secrets_detected: List[str] = field(default_factory=list)
    has_sensitive_files: bool = False
    dependency_changes: List[Dict[str, str]] = field(default_factory=list)
    schema_migrations: List[str] = field(default_factory=list)
    api_changes: List[str] = field(default_factory=list)
    scope_creep_detected: bool = False


@dataclass
class CodeReviewResult:
    approved: bool = False
    score: float = 0.0
    issues: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    requirement_coverage: Dict[str, bool] = field(default_factory=dict)


@dataclass
class CommitPlan:
    type: str = "fix"  # fix, feat, refactor, docs, test
    scope: str = ""
    summary: str = ""
    body: str = ""
    files: List[str] = field(default_factory=list)
    verification: str = ""


@dataclass
class CommitResult:
    created: bool = False
    commit_sha: Optional[str] = None
    message: str = ""
    files: List[str] = field(default_factory=list)
    status: str = "NO_CHANGES"


@dataclass
class PullRequestDraft:
    title: str = ""
    summary: str = ""
    changes: List[str] = field(default_factory=list)
    testing: str = ""
    risk: str = "LOW"
    breaking_changes: List[str] = field(default_factory=list)
    related_issue: Optional[str] = None
    review_notes: str = ""
    formatted_body: str = ""


@dataclass
class EngineeringWorkflowState:
    workflow_id: str = field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    task: Optional[EngineeringTask] = None
    repository_path: str = "."
    base_commit: str = ""
    branch: str = ""
    worktree_path: Optional[str] = None
    issue_analysis: Optional[IssueAnalysis] = None
    change_plan: Optional[Any] = None
    changeset: Dict[str, Any] = field(default_factory=dict)
    test_results: Optional[WorkflowTestEvidence] = None
    review_result: Optional[CodeReviewResult] = None
    commit_plan: Optional[CommitPlan] = None
    commit_result: Optional[CommitResult] = None
    pr_draft: Optional[PullRequestDraft] = None
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    mode: GitWorkflowMode = GitWorkflowMode.PREPARE_ONLY
    dry_run: bool = False
    warnings: List[str] = field(default_factory=list)
    timings: Dict[str, float] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    remote_actions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EngineeringWorkflowResult:
    workflow_id: str
    status: WorkflowStatus
    task: Optional[EngineeringTask]
    branch: str
    base_commit: str
    changeset: Dict[str, Any]
    tests: Optional[WorkflowTestEvidence]
    review: Optional[CodeReviewResult]
    commit: Optional[CommitResult]
    pr_draft: Optional[PullRequestDraft]
    remote_actions: List[Dict[str, Any]]
    warnings: List[str]
    user_facing_summary: str
    timings: Dict[str, float]
    metrics: Dict[str, Any]
    git_safety_metrics: Dict[str, int]
