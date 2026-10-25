from typing import List, Dict, Any
from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    """
    Structured Communication Contract for PlannerAgent outputs.
    """
    project_name: str = Field(default="AIForge Application", description="Software project title")
    domain: str = Field(default="SaaS", description="Detected product domain category")
    executive_summary: str = Field(default="", description="Core product pitch and value proposition")
    requirements: List[str] = Field(default_factory=list, description="All gathered requirements")
    functional_requirements: List[str] = Field(default_factory=list, description="FR-1, FR-2 detailed list")
    non_functional_requirements: List[str] = Field(default_factory=list, description="Performance & security NFRs")
    user_stories: List[str] = Field(default_factory=list, description="User story statements")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions")
    constraints: List[str] = Field(default_factory=list, description="Technical and business constraints")
    features: List[str] = Field(default_factory=list, description="Core feature checklist")
    tasks: List[str] = Field(default_factory=list, description="High-level engineering task breakdown")
    tech_stack: Dict[str, str] = Field(default_factory=dict, description="Recommended technology choices")
