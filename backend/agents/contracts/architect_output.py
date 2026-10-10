from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ArchitectOutput(BaseModel):
    """
    Structured Communication Contract for ArchitectAgent outputs.
    """
    architecture_style: str = Field(default="Modular Monolith", description="Architecture pattern style")
    components: List[str] = Field(default_factory=list, description="Major system components")
    apis: List[Dict[str, str]] = Field(default_factory=list, description="API endpoints definitions")
    database_entities: List[str] = Field(default_factory=list, description="Core database entity models")
    decisions: List[Dict[str, str]] = Field(default_factory=list, description="Architectural decisions with reasons")
    folder_structure: Dict[str, Any] = Field(default_factory=dict, description="Directory tree layout")
    auth_strategy: str = Field(default="JWT Bearer", description="Authentication mechanism")
