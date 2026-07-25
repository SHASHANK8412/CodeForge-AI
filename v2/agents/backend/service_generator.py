"""
AIForge V2 – Service Layer Business Logic Generator
===================================================
Generates Service Layer classes (AuthService, ProjectService, TaskService, GenerationService).
"""

from typing import List
from v2.agents.backend.models import BackendServiceSpec


class FastAPIBackendServiceGenerator:

    def generate_default_services(self, project_name: str) -> List[BackendServiceSpec]:
        return [
            BackendServiceSpec(
                service_name="AuthService",
                responsibility="Handles JWT token generation, password hashing, and user authentication",
                code_content="""import time
import jwt

SECRET_KEY = "aiforge_v2_secret_key"

class AuthService:

    def create_access_token(self, data: dict, expires_delta_sec: int = 86400) -> str:
        payload = data.copy()
        payload["exp"] = time.time() + expires_delta_sec
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    def verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception:
            return None
"""
            ),
            BackendServiceSpec(
                service_name="ProjectService",
                responsibility="Coordinates project creation, complexity evaluation, and lifecycle tracking",
                code_content="""class ProjectService:

    def get_user_projects(self, user_id: str):
        return [
            {"id": "p1", "name": "AI Resume Analyzer", "status": "active"},
            {"id": "p2", "name": "E-Commerce Platform", "status": "in_progress"}
        ]

    def create_project(self, name: str, prompt: str):
        return {"id": "proj_100", "name": name, "prompt": prompt, "status": "created"}
"""
            ),
            BackendServiceSpec(
                service_name="GenerationService",
                responsibility="Orchestrates full-stack AI generation pipeline tasks across agents",
                code_content="""class GenerationService:

    def trigger_generation(self, prompt: str):
        return {"status": "started", "pipeline": "CEO -> Manager -> Planner -> Architect -> Frontend -> Backend"}
"""
            )
        ]


global_service_generator = FastAPIBackendServiceGenerator()
