"""
AIForge Evaluation Engine Models & Data Schemas
===============================================
Provides strongly-typed schemas for Golden Test Cases, Evaluation Results,
Benchmark Performance Reports, and Regression Comparison Reports.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class GoldenTestCase(BaseModel):
    """
    Typed schema for a Golden Test Case in the AIForge evaluation suite.
    """
    id: str = Field(description="Unique identifier for the test case (e.g. EXP_FORMULA1, COD_001)")
    category: str = Field(description="Category: explanation, coding, debugging, general_qa, rag, resume, project, ambiguous")
    prompt: str = Field(description="Input user prompt text")
    expected_intent: str = Field(description="Expected canonical intent taxonomy string")
    expected_agent: str = Field(description="Expected target agent class name")
    expected_profile: str = Field(default="", description="Expected generation profile name")
    required_elements: List[str] = Field(default_factory=list, description="Keywords/concepts required in valid response")
    forbidden_elements: List[str] = Field(default_factory=list, description="Keywords/snippets forbidden in valid response")
    expected_language: Optional[str] = Field(default=None, description="Expected programming language for coding tasks")
    requires_code: bool = Field(default=False, description="True if response must contain code block")
    requires_rag: bool = Field(default=False, description="True if prompt relies on retrieved document context")
    requires_project_workflow: bool = Field(default=False, description="True if prompt triggers full project generation")
    expected_facts: List[str] = Field(default_factory=list, description="Deterministic factual answers for RAG evaluation")
    critical: bool = Field(default=False, description="True if failure triggers CRITICAL REGRESSION status")
    notes: Optional[str] = Field(default="", description="Developer notes explaining test objective")


class TestCaseResult(BaseModel):
    """
    Typed result structure for a single evaluated Golden Test Case.
    """
    test_id: str
    category: str
    prompt: str
    expected_intent: str
    actual_intent: str
    expected_agent: str
    actual_agent: str
    expected_profile: str
    actual_profile: str
    routing_pass: bool
    agent_pass: bool
    profile_pass: bool
    quality_score: float
    contract_pass: bool
    required_elements_pass: bool
    forbidden_elements_pass: bool
    language_match_pass: bool
    rag_facts_pass: bool
    latency_ms: float
    regenerated: bool
    attempts: int
    critical: bool
    overall_pass: bool
    issues: List[str] = Field(default_factory=list)
    response_preview: str = Field(default="")
    full_response: Optional[str] = Field(default=None)


class BenchmarkReport(BaseModel):
    """
    Complete benchmark execution report with aggregate metrics across all 100 golden prompts.
    """
    benchmark_id: str
    timestamp: str
    mode: str  # fast, full, mock
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_pass_rate_pct: float
    routing_accuracy_pct: float
    agent_accuracy_pct: float
    profile_accuracy_pct: float
    average_quality_score: float
    critical_tests_count: int
    critical_tests_passed: int
    critical_tests_pass_pct: float
    regeneration_rate_pct: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    category_scores: Dict[str, float] = Field(default_factory=dict)
    failure_counts_by_type: Dict[str, int] = Field(default_factory=dict)
    results: List[TestCaseResult] = Field(default_factory=list)


class RegressionReport(BaseModel):
    """
    Comparison report between current benchmark run and saved baseline.
    """
    has_regression: bool
    has_critical_regression: bool
    quality_delta: float
    routing_accuracy_delta: float
    pass_rate_delta: float
    latency_delta_ms: float
    regressions_list: List[Dict[str, Any]] = Field(default_factory=list)
    improvements_list: List[Dict[str, Any]] = Field(default_factory=list)
    summary_message: str
