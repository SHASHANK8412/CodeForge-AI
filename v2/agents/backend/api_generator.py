"""
AIForge V2 – FastAPI REST Router & Endpoint Generator
======================================================
Generates FastAPI APIRouters for Authentication, Projects, Tasks, and AI Generation.
"""

from typing import List
from v2.agents.backend.models import BackendAPIEndpoint


class FastAPIRouterGenerator:

    def generate_default_endpoints(self, project_name: str) -> List[BackendAPIEndpoint]:
        return [
            BackendAPIEndpoint(
                path="/api/v1/auth/login",
                method="POST",
                router_name="auth_router",
                summary="User login and JWT bearer token issuance",
                auth_required=False,
                code_content="""from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login_user(req: LoginRequest):
    if req.username == "admin" and req.password == "admin":
        return {"access_token": "mock_jwt_token_2026", "token_type": "bearer", "user": {"name": "Admin User"}}
    return {"access_token": "mock_user_jwt_token", "token_type": "bearer", "user": {"name": req.username}}
"""
            ),
            BackendAPIEndpoint(
                path="/api/v1/auth/register",
                method="POST",
                router_name="auth_router",
                summary="Registers new user account",
                auth_required=False,
                code_content="""from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register")
def register_user(req: RegisterRequest):
    return {"status": "created", "username": req.username, "email": req.email}
"""
            ),
            BackendAPIEndpoint(
                path="/api/v1/projects",
                method="GET",
                router_name="projects_router",
                summary="Lists user projects",
                auth_required=True,
                code_content="""from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("")
def list_projects():
    return [
        {"id": "p1", "name": "AI Resume Analyzer", "status": "active", "complexity": "medium"},
        {"id": "p2", "name": "E-Commerce Platform", "status": "in_progress", "complexity": "enterprise"}
    ]
"""
            ),
            BackendAPIEndpoint(
                path="/api/v1/projects",
                method="POST",
                router_name="projects_router",
                summary="Creates a new software project",
                auth_required=True,
                code_content="""from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["Projects"])

class CreateProjectRequest(BaseModel):
    name: str
    prompt: str

@router.post("")
def create_project(req: CreateProjectRequest):
    return {"id": "p_new_100", "name": req.name, "status": "created"}
"""
            ),
            BackendAPIEndpoint(
                path="/api/v1/generate/project",
                method="POST",
                router_name="generate_router",
                summary="Executes autonomous AI software generation pipeline",
                auth_required=True,
                code_content="""from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/generate", tags=["AI Generation"])

class GenerationRequest(BaseModel):
    prompt: str

@router.post("/project")
def generate_project(req: GenerationRequest):
    return {"status": "accepted", "project_id": "proj_v2_auto", "message": "Autonomous generation pipeline triggered."}
"""
            )
        ]


global_api_generator = FastAPIRouterGenerator()
