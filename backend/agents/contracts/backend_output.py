from typing import List, Dict, Any
from pydantic import BaseModel, Field


class BackendOutput(BaseModel):
    """
    Structured Communication Contract for BackendAgent outputs.
    """
    endpoints: List[str] = Field(default_factory=list, description="Defined REST API endpoints")
    auth_strategy: str = Field(default="JWT", description="Security authentication strategy")
    folder_structure: List[str] = Field(default_factory=list, description="Backend module hierarchy")
    code_files: Dict[str, str] = Field(default_factory=dict, description="Filename to Python code mapping")
