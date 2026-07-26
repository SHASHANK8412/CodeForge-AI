"""
AIForge V2 – Backend Agent Data Models
======================================
Data structures for FastAPI Routers, Services, Repositories, Authentication, Middleware, Validation, and Unit Tests.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BackendAPIEndpoint(BaseModel):
    path: str
    method: str  # GET, POST, PUT, DELETE
    router_name: str
    summary: str
    auth_required: bool = True
    code_content: str


class BackendServiceSpec(BaseModel):
    service_name: str
    responsibility: str
    code_content: str


class BackendRepositorySpec(BaseModel):
    repository_name: str
    entity_name: str
    code_content: str


class BackendMiddlewareSpec(BaseModel):
    middleware_name: str
    purpose: str
    code_content: str


class BackendAuthSpec(BaseModel):
    auth_type: str = "JWT Bearer / OAuth2"
    roles: List[str] = Field(default_factory=lambda: ["Admin", "Developer", "Viewer"])
    permissions: List[str] = Field(default_factory=lambda: ["read", "write", "delete", "deploy"])
    code_content: str


class BackendTestSpec(BaseModel):
    test_name: str
    target_module: str
    code_content: str


class BackendReport(BaseModel):
    project_id: str
    project_name: str
    folder_structure: List[str]
    apis: List[BackendAPIEndpoint]
    services: List[BackendServiceSpec]
    repositories: List[BackendRepositorySpec]
    auth: BackendAuthSpec
    middleware: List[BackendMiddlewareSpec]
    validation_schemas: Dict[str, Any] = Field(default_factory=dict)
    tests: List[BackendTestSpec]
    main_py_content: str
    dependencies: List[str] = Field(
        default_factory=lambda: ["fastapi", "uvicorn", "pydantic", "pyjwt", "passlib[bcrypt]", "sqlalchemy", "pytest"]
    )
    build_status: str = "success"
    confidence_score: float = 97.5
