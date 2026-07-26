"""
AIForge V2 – Repository Layer Persistence Generator
===================================================
Generates Repository Layer classes (UserRepository, ProjectRepository, TaskRepository).
"""

from typing import List
from v2.agents.backend.models import BackendRepositorySpec


class FastAPIBackendRepositoryGenerator:

    def generate_default_repositories(self, project_name: str) -> List[BackendRepositorySpec]:
        return [
            BackendRepositorySpec(
                repository_name="UserRepository",
                entity_name="User",
                code_content="""class UserRepository:

    def find_by_id(self, user_id: str):
        return {"id": user_id, "username": "admin", "role": "admin"}

    def find_by_username(self, username: str):
        return {"id": "u1", "username": username, "role": "admin"}
"""
            ),
            BackendRepositorySpec(
                repository_name="ProjectRepository",
                entity_name="Project",
                code_content="""class ProjectRepository:

    def get_all(self):
        return [{"id": "p1", "name": "AI Resume Analyzer"}]

    def save(self, project_data: dict):
        return {"id": project_data.get("id", "p100"), **project_data}
"""
            )
        ]


global_repository_generator = FastAPIBackendRepositoryGenerator()
