from typing import List, Dict, Any
from pydantic import BaseModel, Field


class TestingOutput(BaseModel):
    """
    Structured Communication Contract for TestingAgent outputs.
    """
    total: int = Field(default=0, description="Total generated test functions count")
    passed: int = Field(default=0, description="Passed tests count")
    failed: int = Field(default=0, description="Failed tests count")
    coverage: float = Field(default=85.0, description="Code coverage percentage")
    failures: List[str] = Field(default_factory=list, description="Test failure descriptions")
    code: str = Field(default="", description="Pytest test suite code text")
