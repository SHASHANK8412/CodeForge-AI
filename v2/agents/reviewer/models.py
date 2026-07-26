"""
AIForge V2 – Reviewer Agent Data Models
=======================================
Data structures for Code Review Issues, Refactoring Suggestions, Category Scores,
Security Vulnerability Audits, and Quality Metrics.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ReviewCategoryScore(BaseModel):
    category_name: str  # Architecture, Frontend, Backend, Database, Security, Performance, Maintainability
    score: float  # 0-100
    status: str = "passed"
    suggestions: List[str] = Field(default_factory=list)


class ReviewIssue(BaseModel):
    issue_id: str
    category: str
    severity: str  # Critical, High, Medium, Low
    description: str
    target_file: Optional[str] = None
    resolved: bool = False


class RefactorSuggestion(BaseModel):
    file: str
    description: str
    priority: str  # High, Medium, Low
    code_before: str = ""
    code_after: str = ""


class QualityMetrics(BaseModel):
    maintainability_index: float = 95.0
    cyclomatic_complexity: float = 4.2
    doc_coverage_pct: float = 92.5
    code_duplication_pct: float = 2.1
    overall_score: float = 95.5


class ReviewReport(BaseModel):
    project_id: str
    project_name: str
    category_scores: List[ReviewCategoryScore]
    issues: List[ReviewIssue]
    refactorings: List[RefactorSuggestion]
    metrics: QualityMetrics
    overall_score: float = 95.5
    build_status: str = "approved"
    confidence_score: float = 98.0
