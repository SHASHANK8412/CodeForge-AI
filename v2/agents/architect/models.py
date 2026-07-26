"""
AIForge V2 – Architect Agent Data Models
=========================================
Data structures for System Components, API Specifications, Database Schemas, ER Diagrams,
Folder Trees, Security Strategies, Caching Strategies, VectorStore Collections, and Deployment.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SystemComponent(BaseModel):
    name: str
    type: str  # Frontend, API Gateway, Microservice, Database, Cache, MessageQueue
    responsibility: str
    dependencies: List[str] = Field(default_factory=list)


class APISpecification(BaseModel):
    endpoint: str
    method: str  # GET, POST, PUT, DELETE
    description: str
    request_schema: Dict[str, Any] = Field(default_factory=dict)
    response_schema: Dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = True


class ColumnDefinition(BaseModel):
    name: str
    data_type: str  # VARCHAR, INTEGER, BOOLEAN, TIMESTAMP, JSONB
    primary_key: bool = False
    nullable: bool = True
    foreign_key: Optional[str] = None


class TableDefinition(BaseModel):
    table_name: str
    description: str
    columns: List[ColumnDefinition]
    indexes: List[str] = Field(default_factory=list)


class DatabaseSchemaSpec(BaseModel):
    engine: str = "PostgreSQL"
    tables: List[TableDefinition]
    er_relationships: List[str] = Field(default_factory=list)


class SecurityStrategy(BaseModel):
    auth_type: str = "OAuth2 / JWT Bearer"
    encryption: str = "TLS 1.3 & AES-256"
    rate_limiting: str = "100 req/min per IP via Redis"
    protections: List[str] = Field(
        default_factory=lambda: ["SQL Injection Protection", "XSS Sanitization", "CSRF Tokens", "RBAC Auth"]
    )


class CacheStrategySpec(BaseModel):
    engine: str = "Redis"
    cached_entities: List[str] = Field(
        default_factory=lambda: ["User Sessions", "Planner Reports", "LLM Generation Cache", "API Responses"]
    )
    ttl_seconds: int = 3600


class VectorStoreSpec(BaseModel):
    engine: str = "ChromaDB"
    collections: List[str] = Field(
        default_factory=lambda: ["knowledge_base", "project_docs", "code_embeddings", "experience_memory"]
    )
    vector_dims: int = 384


class DeploymentArchitecture(BaseModel):
    provider: str = "Docker / Docker Compose"
    containers: List[str] = Field(
        default_factory=lambda: ["frontend-react", "backend-fastapi", "postgres-db", "redis-cache", "chroma-vector"]
    )
    compose_services: Dict[str, Any] = Field(default_factory=dict)


class ArchitectureReport(BaseModel):
    project_id: str
    project_name: str
    high_level_architecture: str
    low_level_architecture: str
    folder_structure: List[str]
    components: List[SystemComponent]
    apis: List[APISpecification]
    database: DatabaseSchemaSpec
    security: SecurityStrategy
    caching: CacheStrategySpec
    vector_store: VectorStoreSpec
    deployment: DeploymentArchitecture
    risks: List[str] = Field(default_factory=list)
    confidence_score: float = 95.0
