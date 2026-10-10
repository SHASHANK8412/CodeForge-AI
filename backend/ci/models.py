"""
AIForge Autonomous CI/CD Pipeline Models
=======================================
Typed schemas for CI pipeline execution, stages, failure telemetry,
repaired patch history, and GitHub Actions workflow generation.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CIStageType(str, Enum):
    DEPENDENCIES = "dependencies"
    BUILD = "build"
    TEST = "tests"
    LINT = "lint"
    SECURITY = "security"


class CIStageStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class CIOverallStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class CIStageResult(BaseModel):
    __test__ = False
    stage: str = Field(description="Stage name e.g. dependencies, build, tests, lint, security")
    status: str = Field(default="passed", description="Outcome: passed, failed, warning, skipped, timeout")
    exit_code: int = Field(default=0, description="Process exit code")
    stdout: str = Field(default="", description="Captured stdout")
    stderr: str = Field(default="", description="Captured stderr")
    duration: float = Field(default=0.0, description="Execution duration in seconds")
    command: str = Field(default="", description="Command executed in sandbox")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured stage details (e.g. findings, metrics)")


class CIConfig(BaseModel):
    __test__ = False
    max_repair_attempts: int = Field(default=3, description="Maximum self-debugging retry iterations")
    timeout_seconds: float = Field(default=30.0, description="Execution timeout in seconds per stage")
    execution_backend: str = Field(default="local", description="Backend sandbox: 'local' or 'docker'")
    docker_enabled: bool = Field(default=False, description="Whether Docker container isolation is active")
    memory_limit: str = Field(default="512m", description="Memory quota limit")
    cpu_limit: float = Field(default=1.0, description="CPU quota limit")
    network_mode: str = Field(default="none", description="Network isolation mode e.g. 'none', 'bridge'")
    generate_github_workflow: bool = Field(default=True, description="Whether to generate .github/workflows/aiforge-ci.yml")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Custom environment variables")


class CIPipelineResult(BaseModel):
    __test__ = False
    run_id: str = Field(default_factory=lambda: f"ci_{uuid.uuid4().hex[:10]}", description="Unique CI run identifier")
    project_id: str = Field(default="default_project", description="Target project identifier")
    project_type: str = Field(default="python", description="Detected language/framework")
    commit_version: str = Field(default="main", description="Git commit SHA or branch version")
    status: str = Field(default="PASSED", description="Overall CI status: PASSED, FAILED, TIMEOUT, CANCELLED")
    build: Dict[str, Any] = Field(default_factory=dict, description="Build stage outcome")
    tests: Dict[str, Any] = Field(default_factory=dict, description="Test stage outcome")
    lint: Dict[str, Any] = Field(default_factory=dict, description="Lint stage outcome")
    security: Dict[str, Any] = Field(default_factory=dict, description="Security stage outcome")
    dependencies: Dict[str, Any] = Field(default_factory=dict, description="Dependency stage outcome")
    repair_attempts: int = Field(default=0, description="Count of automatic self-debugging repair cycles performed")
    max_repair_attempts: int = Field(default=3, description="Max allowed repair attempts")
    duration: float = Field(default=0.0, description="Total pipeline execution duration in seconds")
    stages: List[CIStageResult] = Field(default_factory=list, description="Ordered stage results")
    applied_repairs: List[Dict[str, Any]] = Field(default_factory=list, description="Repairs applied by Debug Agent")
    files_modified: List[str] = Field(default_factory=list, description="List of modified project files")
    workflow_yaml: str = Field(default="", description="Generated GitHub Actions workflow content")
    backend_used: str = Field(default="local", description="Backend sandbox used: 'docker' or 'local'")
    container_id: Optional[str] = Field(default=None, description="Docker container ID if executed inside Docker")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp")


class CIRunHistoryItem(BaseModel):
    __test__ = False
    run_id: str = Field(description="Unique CI run identifier")
    project_id: str = Field(description="Associated project identifier")
    timestamp: str = Field(description="Execution timestamp")
    commit_version: str = Field(default="main", description="Target commit or branch")
    overall_status: str = Field(description="PASSED, FAILED, TIMEOUT, CANCELLED")
    repair_attempts: int = Field(default=0, description="Repairs performed")
    duration: float = Field(default=0.0, description="Duration in seconds")
    stage_summaries: Dict[str, str] = Field(default_factory=dict, description="Summary mapping of stage -> status")
    backend_used: str = Field(default="local", description="Sandbox backend used")

    @property
    def status(self) -> str:
        return self.overall_status
