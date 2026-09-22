"""
AIForge V2 — Day 14 Quality Gates & Finding Schema
==================================================
Defines structured quality gates, finding severity/categories, and gate evaluation logic.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GateStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingCategory(str, Enum):
    REQUIREMENTS = "REQUIREMENTS"
    ARCHITECTURE = "ARCHITECTURE"
    CODE_QUALITY = "CODE_QUALITY"
    SECURITY = "SECURITY"
    TESTING = "TESTING"
    PERFORMANCE = "PERFORMANCE"
    DOCUMENTATION = "DOCUMENTATION"
    SYNTAX = "SYNTAX"
    DATABASE = "DATABASE"
    API = "API"


class Finding(BaseModel):
    id: str = Field(..., description="Unique finding ID, e.g., finding_123")
    severity: FindingSeverity
    category: FindingCategory
    file: Optional[str] = Field(default=None, description="Affected file path")
    line: Optional[int] = Field(default=None, description="Line number if applicable")
    message: str = Field(..., description="Defect description")
    suggested_fix: str = Field(default="", description="Recommended remediation action")
    blocking: bool = Field(default=False, description="True if this finding blocks deployment")


class QualityGate(BaseModel):
    name: str = Field(..., description="Gate name, e.g., 'Requirements' or 'Security'")
    status: GateStatus = GateStatus.PASS
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    findings: List[Finding] = Field(default_factory=list)
    blocking: bool = Field(default=True, description="True if failure blocks release")


class QualityReport(BaseModel):
    overall_score: float = Field(default=100.0)
    overall_status: GateStatus = GateStatus.PASS
    deployment_allowed: bool = True
    gates: Dict[str, QualityGate] = Field(default_factory=dict)
    findings: List[Finding] = Field(default_factory=list)


def evaluate_quality_gates(
    findings: List[Finding],
    test_results: Optional[Dict[str, Any]] = None,
    quality_score: float = 100.0
) -> QualityReport:
    """
    Evaluates all 7 Quality Gates based on findings and test performance:
    1. Requirements
    2. Architecture
    3. Code Quality
    4. Security
    5. Testing
    6. Performance
    7. Documentation
    """
    gate_names = ["requirements", "architecture", "code_quality", "security", "testing", "performance", "documentation"]
    gates: Dict[str, QualityGate] = {
        g: QualityGate(name=g.replace("_", " ").title(), status=GateStatus.PASS, score=100.0, blocking=True)
        for g in gate_names
    }

    # Assign findings to respective gates
    for f in findings:
        cat_key = f.category.value.lower()
        if cat_key in gates:
            gates[cat_key].findings.append(f)
            # Reduce gate score based on severity
            penalty = {"CRITICAL": 35.0, "HIGH": 20.0, "MEDIUM": 10.0, "LOW": 5.0, "INFO": 1.0}.get(f.severity.value, 5.0)
            gates[cat_key].score = max(0.0, gates[cat_key].score - penalty)
            if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH) or f.blocking:
                gates[cat_key].status = GateStatus.FAIL
            elif gates[cat_key].status != GateStatus.FAIL and f.severity == FindingSeverity.MEDIUM:
                gates[cat_key].status = GateStatus.WARN

    # Process testing gate specifically
    if test_results:
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        test_score = (passed / total * 100.0) if total > 0 else (100.0 if not test_results.get("error") else 0.0)
        gates["testing"].score = round(test_score, 1)

        if failed > 0 or test_results.get("error"):
            gates["testing"].status = GateStatus.FAIL
            gates["testing"].findings.append(Finding(
                id=f"finding_test_{failed}",
                severity=FindingSeverity.HIGH if failed > 0 else FindingSeverity.CRITICAL,
                category=FindingCategory.TESTING,
                message=f"Test suite has {failed} failing test(s).",
                suggested_fix="Fix failing assertions and code exceptions.",
                blocking=True
            ))

    # Determine overall status and deployment readiness
    blocking_failed = any(g.status == GateStatus.FAIL and g.blocking for g in gates.values())
    any_warns = any(g.status == GateStatus.WARN for g in gates.values())

    overall_status = GateStatus.FAIL if blocking_failed else (GateStatus.WARN if any_warns else GateStatus.PASS)
    deployment_allowed = not blocking_failed

    avg_score = round(sum(g.score for g in gates.values()) / len(gates), 1)

    return QualityReport(
        overall_score=avg_score,
        overall_status=overall_status,
        deployment_allowed=deployment_allowed,
        gates=gates,
        findings=findings
    )
