from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ReviewOutput(BaseModel):
    """
    Structured Communication Contract for ReviewerAgent outputs.
    """
    score: float = Field(default=95.0, description="Overall code review quality score (0-100)")
    findings: List[str] = Field(default_factory=list, description="Specific code review findings")
    recommendations: List[str] = Field(default_factory=list, description="Actionable improvement recommendations")
