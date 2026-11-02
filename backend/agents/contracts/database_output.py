from typing import List, Dict, Any
from pydantic import BaseModel, Field


class DatabaseOutput(BaseModel):
    """
    Structured Communication Contract for DatabaseAgent outputs.
    """
    tables: List[str] = Field(default_factory=list, description="SQL table names")
    schema_sql: str = Field(default="", description="PostgreSQL 3NF SQL DDL schema text")
    migrations: List[str] = Field(default_factory=list, description="Schema migration steps")
    code_files: Dict[str, str] = Field(default_factory=dict, description="Database scripts mapping")
