from typing import List, Dict, Any
from pydantic import BaseModel, Field


class FrontendOutput(BaseModel):
    """
    Structured Communication Contract for FrontendAgent outputs.
    """
    components: List[str] = Field(default_factory=list, description="React component names")
    routing: List[str] = Field(default_factory=list, description="Application routes")
    folder_structure: List[str] = Field(default_factory=list, description="Frontend folder layout")
    code_files: Dict[str, str] = Field(default_factory=dict, description="Filename to content mapping")
