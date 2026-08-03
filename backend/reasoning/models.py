"""
AIForge Adaptive Reasoning Models
==================================
Typed schemas for Task Complexity Levels, Execution Strategies,
Complexity Results, and Structured Task Plans.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    """
    Categorical scale of task complexity.
    """
    TRIVIAL = "TRIVIAL"      # Extremely direct factual / short query
    SIMPLE = "SIMPLE"        # Normal single-agent single-step request
    MODERATE = "MODERATE"    # Requires lightweight task decomposition & planning
    COMPLEX = "COMPLEX"      # Multi-step reasoning across components
    WORKFLOW = "WORKFLOW"    # Full multi-agent LangGraph autonomous project workflow


class ExecutionStrategy(str, Enum):
    """
    Execution strategy selected by AIForge based on complexity and intent.
    """
    DIRECT = "DIRECT"        # Minimal fast generation (no planning, no extra overhead)
    STANDARD = "STANDARD"    # Normal specialized agent pipeline
    PLANNED = "PLANNED"      # Internal structured TaskPlan execution
    WORKFLOW = "WORKFLOW"    # LangGraph multi-agent autonomous engineering workflow


class ComplexityResult(BaseModel):
    """
    Typed result returned by ComplexityAnalyzer.
    Internal signals only; private reasoning traces are never exposed to the user.
    """
    level: ComplexityLevel = Field(description="Categorical complexity level")
    score: float = Field(description="Normalized complexity score (0.0 to 1.0)")
    strategy: ExecutionStrategy = Field(description="Recommended execution strategy")
    signals: List[str] = Field(default_factory=list, description="Short label indicators contributing to score")
    confidence: float = Field(default=0.90, description="Confidence in complexity classification")
    requires_planning: bool = Field(default=False, description="True if internal TaskPlan should be constructed")
    requires_workflow: bool = Field(default=False, description="True if full multi-agent project workflow is required")
    override_applied: Optional[str] = Field(default=None, description="Name of intent override rule applied if any")


class TaskPlanStep(BaseModel):
    """
    A single step within a structured TaskPlan.
    """
    id: int = Field(description="Step sequence number (1-indexed)")
    description: str = Field(description="Actionable task step description")
    agent_hint: Optional[str] = Field(default="CodingAgent", description="Suggested agent role")
    status: str = Field(default="pending", description="Status: 'pending', 'completed', 'skipped'")


class TaskPlan(BaseModel):
    """
    Structured internal execution plan for PLANNED strategy.
    Exposes zero hidden chain-of-thought traces.
    """
    goal: str = Field(description="Concise primary engineering objective")
    steps: List[TaskPlanStep] = Field(default_factory=list, description="Ordered sequence of execution steps (3 to 6 typical, max 8)")
    constraints: List[str] = Field(default_factory=list, description="Engineering constraints or boundaries")
    dependencies: List[str] = Field(default_factory=list, description="Required technologies or prerequisites")
    expected_output: str = Field(default="", description="Summary of expected deliverable artifact")
    is_valid: bool = Field(default=True, description="True if plan passed PlanValidator")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Internal plan metadata")
