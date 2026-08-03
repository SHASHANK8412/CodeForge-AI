"""
AIForge Secure Execution Sandbox & Self-Debugging Models
=========================================================
Typed schemas for Execution Decisions, Code Artifacts, Sandbox Execution Results,
Test Plans, Test Results, Failure Analysis, and Verification Status.
"""

import uuid
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
    """
    Structured test plan.
    """
    test_type: str = Field(default="UNIT", description="Test suite type")
    language: str = Field(default="python", description="Language under test")
    test_cases: List[Dict[str, Any]] = Field(default_factory=list, description="List of test case dictionaries")
    command: str = Field(default="", description="Trusted test runner command")
    timeout_seconds: float = Field(default=10.0, description="Test execution timeout")


class TestResult(BaseModel):
    """
    Structured test suite execution outcome.
    """
    passed: int = Field(default=0, description="Count of passed tests")
    failed: int = Field(default=0, description="Count of failed tests")
    total: int = Field(default=0, description="Total count of evaluated tests")
    errors: List[str] = Field(default_factory=list, description="List of failure messages")
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
