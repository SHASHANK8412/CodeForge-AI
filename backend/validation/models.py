from typing import List, Dict, Any
from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    validator: str
    status: str  # "PASS" or "FAIL"
    score: float
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QualityScore(BaseModel):
    overall_score: float
    grade: str  # A+, A, B+, B, FAIL
    ready_for_export: bool

class ValidationReport(BaseModel):
    timestamp: str
    project_name: str
    results: List[ValidationResult]
    quality: QualityScore
    summary: Dict[str, Any] = Field(default_factory=dict)
