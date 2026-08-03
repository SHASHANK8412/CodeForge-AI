"""
AIForge Quality Validation Models & Data Structures
===================================================
Provides strongly-typed models for validation results, quality scoring, severity assessment, and configuration thresholds.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """
    Typed result structure emitted by OutputValidator.
    Never pass unstructured dictionaries throughout the system.
    """
    is_valid: bool = Field(description="True if the response passes all quality gates")
    score: float = Field(ge=0.0, le=1.0, description="Overall quality score from 0.0 to 1.0")
    severity: str = Field(default="low", description="Severity level: 'low', 'medium', 'high', 'critical'")
    should_regenerate: bool = Field(default=False, description="True if automatic regeneration should be triggered")
    issues: List[str] = Field(default_factory=list, description="List of hard failure reasons/contract violations")
    warnings: List[str] = Field(default_factory=list, description="List of soft quality warnings")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Breakdown of individual check outcomes")
    dimension_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Detailed dimension scores: relevance, task_fulfillment, contract_match, completeness, format_validity, non_repetition"
    )
    latency_ms: float = Field(default=0.0, description="Validation latency in milliseconds")


class QualityConfig(BaseModel):
    """
    Configurable thresholds for quality validation and controlled regeneration.
    Eliminates magic numbers scattered across the codebase.
    """
    pass_score: float = Field(default=0.75, description="Score threshold for accepting a response")
    regen_score: float = Field(default=0.55, description="Score threshold below which regeneration is required")
    max_regenerations: int = Field(default=1, description="Maximum automatic regeneration attempts per user request")
    enable_llm_judge: bool = Field(default=False, description="Enable optional LLM judge for borderline scores (0.55 - 0.75)")
    dev_mode: bool = Field(default=True, description="Attach quality metadata in API response")
