"""
AIForge V2 – Testing Agent Data Models
======================================
Data structures for Test Cases, Coverage Reports, Performance Benchmarks,
Security Scans, and Execution Results.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TestCaseSpec(BaseModel):
    test_name: str
    test_type: str  # Unit, Integration, API, DB, E2E, Performance, Security
    target_module: str
    code_content: str
    status: str = "passed"  # passed, failed, skipped
    execution_time_ms: float = 15.0


class CoverageReportSpec(BaseModel):
    line_coverage_pct: float = 94.5
    branch_coverage_pct: float = 91.0
    function_coverage_pct: float = 96.0
    overall_coverage_pct: float = 94.2


class PerformanceTestMetrics(BaseModel):
    avg_response_time_ms: float = 12.4
    p95_latency_ms: float = 28.5
    throughput_rps: float = 450.0
    error_rate_pct: float = 0.0


class SecurityTestMetrics(BaseModel):
    sql_injection_vulnerabilities: int = 0
    xss_vulnerabilities: int = 0
    csrf_vulnerabilities: int = 0
    rbac_issues: int = 0


class TestingReport(BaseModel):
    project_id: str
    project_name: str
    unit_tests: List[TestCaseSpec]
    integration_tests: List[TestCaseSpec]
    api_tests: List[TestCaseSpec]
    database_tests: List[TestCaseSpec]
    e2e_tests: List[TestCaseSpec]
    performance_tests: List[TestCaseSpec]
    security_tests: List[TestCaseSpec]
    coverage: CoverageReportSpec
    performance_metrics: PerformanceTestMetrics
    security_metrics: SecurityTestMetrics
    overall_status: str = "PASSED"
    passed_count: int = 24
    failed_count: int = 0
    confidence_score: float = 98.5
