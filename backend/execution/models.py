"""
AIForge Secure Execution Sandbox & Self-Debugging Models
=========================================================
Typed schemas for Execution Decisions, Code Artifacts, Sandbox Execution Results,
Test Plans, Test Results, Failure Analysis, and Verification Status.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field



class ExecutionType(str, Enum):
    STATIC_ONLY = "STATIC_ONLY"
    SYNTAX_CHECK = "SYNTAX_CHECK"
    COMPILE = "COMPILE"
    RUN = "RUN"
    TEST = "TEST"
    PROJECT_TEST = "PROJECT_TEST"
    UNSUPPORTED = "UNSUPPORTED"


class ExecutionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    TIMEOUT = "TIMEOUT"
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    SECURITY_BLOCK = "SECURITY_BLOCK"
    UNSUPPORTED = "UNSUPPORTED"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    EXECUTION_UNAVAILABLE = "EXECUTION_UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"


class CodeArtifact(BaseModel):
    """
    Structured executable code artifact.
    """
    filename: str = Field(description="Filename with extension (e.g. main.py, Solution.java)")
    language: str = Field(description="Language identifier (python, javascript, java, cpp)")
    content: str = Field(description="Raw code content")
    purpose: str = Field(default="SOURCE", description="Purpose: 'SOURCE', 'TEST', 'CONFIG', 'DEPENDENCY'")


class ExecutionDecision(BaseModel):
    """
    Decision returned by ExecutionEligibilityChecker.
    """
    should_execute: bool = Field(description="True if code is eligible for sandbox execution")
    execution_type: ExecutionType = Field(default=ExecutionType.RUN, description="Execution classification type")
    language: str = Field(default="python", description="Target programming language")
    reason: str = Field(default="EXECUTABLE_CODE", description="Categorical reason label")


class ExecutionLimits(BaseModel):
    """
    Resource limits for isolated sandbox execution.
    """
    timeout_seconds: float = Field(default=10.0, description="Max execution timeout in seconds")
    memory_mb: int = Field(default=512, description="Max RAM allocation in MB")
    cpu_count: float = Field(default=1.0, description="Max CPU core usage limit")
    max_output_bytes: int = Field(default=50000, description="Max stdout/stderr captured bytes")
    network_enabled: bool = Field(default=False, description="Default network access disabled")


class ExecutionResult(BaseModel):
    """
    Captured execution outcome from SandboxExecutor.
    """
    status: ExecutionStatus = Field(description="Execution status enum")
    exit_code: int = Field(default=0, description="Process exit code")
    stdout: str = Field(default="", description="Captured stdout")
    stderr: str = Field(default="", description="Captured stderr")
    duration_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    timed_out: bool = Field(default=False, description="True if process timed out")
    memory_exceeded: bool = Field(default=False, description="True if memory limit exceeded")
    output_truncated: bool = Field(default=False, description="True if stdout/stderr was truncated")
    language: str = Field(default="python", description="Language executed")
    execution_type: str = Field(default="RUN", description="Execution type string")
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique execution run ID")


class TestPlan(BaseModel):
    __test__ = False
    test_type: str = Field(default="UNIT", description="Test suite type")
    language: str = Field(default="python", description="Language under test")
    test_cases: List[Dict[str, Any]] = Field(default_factory=list, description="List of test case dictionaries")
    command: str = Field(default="", description="Trusted test runner command")
    timeout_seconds: float = Field(default=10.0, description="Test execution timeout")


class TestFailureDetail(BaseModel):
    __test__ = False
    test_name: str = Field(default="unknown_test", description="Failed test function or case name")
    error: str = Field(default="", description="Error/exception message")
    file: str = Field(default="", description="Path to file where failure occurred")
    line: Optional[int] = Field(default=None, description="Line number of failure")
    requirement: str = Field(default="", description="Affected functional requirement if known")


class TestResult(BaseModel):
    __test__ = False
    success: bool = Field(default=True, description="True if test suite passed completely")

    passed: int = Field(default=0, description="Count of passed tests")
    failed: int = Field(default=0, description="Count of failed tests")
    total: int = Field(default=0, description="Total count of evaluated tests")
    failures: List[TestFailureDetail] = Field(default_factory=list, description="Structured list of failure details")
    errors: List[str] = Field(default_factory=list, description="List of failure messages")
    coverage: Optional[float] = Field(default=None, description="Test coverage percentage")
    summary: str = Field(default="", description="Human-readable verification summary")
    duration_ms: float = Field(default=0.0, description="Test run duration in ms")
    execution_result: Optional[ExecutionResult] = Field(default=None, description="Raw execution result")



class FailureAnalysis(BaseModel):
    """
    Structured analysis of execution or test failure.
    """
    failure_type: str = Field(description="Category: SYNTAX_ERROR, ASSERTION_FAILURE, TIMEOUT, BOUNDARY_ERROR, etc.")
    summary: str = Field(description="Concise description of the failure cause")
    likely_location: str = Field(description="Location of bug in code")
    action: str = Field(description="Suggested fix action")


class PatchResult(BaseModel):
    """
    Result of a code repair patch attempt.
    """
    changed_files: List[str] = Field(default_factory=list, description="List of modified files")
    summary: str = Field(description="Brief patch summary")
    code: str = Field(description="Patched code content")
    improved: bool = Field(default=False, description="True if patch changed code")


class DebugResult(BaseModel):
    __test__ = False
    success: bool = Field(default=True, description="True if diagnosis and targeted fix was identified")
    diagnosis: str = Field(default="", description="High-level diagnosis summary")
    root_cause: str = Field(default="", description="Exact technical root cause explanation")
    error_type: str = Field(default="UNKNOWN", description="Category: SYNTAX_ERROR, IMPORT_ERROR, ASSERTION_FAILURE, API_MISMATCH, etc.")
    files_to_modify: List[str] = Field(default_factory=list, description="List of relative file paths needing modification")
    changes: Dict[str, str] = Field(default_factory=dict, description="Mapping of relative file path -> proposed updated content")
    confidence: float = Field(default=1.0, description="Confidence score between 0.0 and 1.0")
    explanation: str = Field(default="", description="Detailed fix explanation")


class MemoryRecord(BaseModel):
    __test__ = False
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique memory record ID")
    project_id: str = Field(default="default_project", description="Associated project ID")
    session_id: str = Field(default="", description="Session ID")
    memory_type: str = Field(default="FAILURE", description="Category: PROJECT, FAILURE, PATTERN")
    content: str = Field(default="", description="Text representation for search and display")
    error_type: str = Field(default="", description="Category: SYNTAX_ERROR, IMPORT_ERROR, ASSERTION_FAILURE, etc.")
    technology: str = Field(default="", description="Tech stack tags e.g. FastAPI, PostgreSQL, React, Node")
    files: List[str] = Field(default_factory=list, description="Associated file paths")
    root_cause: str = Field(default="", description="Extracted root cause")
    fix: str = Field(default="", description="Fix content or description")
    result: str = Field(default="PASS", description="Execution/test result: PASS or FAIL")
    confidence: float = Field(default=1.0, description="Confidence score between 0.0 and 1.0")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp")


class ExportValidationResult(BaseModel):
    __test__ = False
    allowed: bool = Field(default=False, description="True if project is verified and allowed to export")
    reason: str = Field(default="", description="Human-readable reason for export permission or denial")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Detailed dictionary of individual verification checks")
    verification_hash: str = Field(default="", description="MD5 hash of project files at verification time")
    verified_at: Optional[str] = Field(default=None, description="ISO timestamp when verification passed")


class ExportResult(BaseModel):
    __test__ = False
    success: bool = Field(default=False, description="True if export completed successfully")
    export_type: str = Field(default="ZIP", description="ZIP, GITHUB, DOCS")
    project_name: str = Field(default="", description="Project name")
    path: Optional[str] = Field(default=None, description="Output zip path or repository URL")
    reason: str = Field(default="", description="Status or denial reason")





