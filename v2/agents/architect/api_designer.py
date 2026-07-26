"""
AIForge V2 – REST API Designer
==============================
Generates REST endpoints, HTTP methods, request/response schemas, and auth requirements.
"""

from typing import List, Dict, Any
from v2.agents.architect.models import APISpecification


class APIDesigner:

    def generate_api_specs(self, project_name: str) -> List[APISpecification]:
        return [
            APISpecification(
                endpoint="/api/v1/auth/login",
                method="POST",
                description="Authenticates user credentials and returns JWT bearer token.",
                request_schema={"username": "string", "password": "string"},
                response_schema={"access_token": "string", "token_type": "bearer", "expires_in": 86400},
                auth_required=False
            ),
            APISpecification(
                endpoint="/api/v1/auth/register",
                method="POST",
                description="Registers new user account.",
                request_schema={"email": "string", "username": "string", "password": "string"},
                response_schema={"id": "string", "username": "string", "status": "created"},
                auth_required=False
            ),
            APISpecification(
                endpoint="/api/v1/projects",
                method="GET",
                description="Lists active projects for authenticated user.",
                request_schema={},
                response_schema={"projects": [{"id": "string", "name": "string", "status": "string"}]},
                auth_required=True
            ),
            APISpecification(
                endpoint="/api/v1/project/start",
                method="POST",
                description="Initiates project generation pipeline.",
                request_schema={"prompt": "string"},
                response_schema={"project_id": "string", "status": "started"},
                auth_required=True
            ),
            APISpecification(
                endpoint="/api/v1/planner/analyze",
                method="POST",
                description="Generates Product Blueprint report.",
                request_schema={"prompt": "string"},
                response_schema={"requirements": {}, "user_stories": []},
                auth_required=True
            ),
            APISpecification(
                endpoint="/api/v1/architect/design",
                method="POST",
                description="Generates technical architecture design package.",
                request_schema={"prompt": "string"},
                response_schema={"architecture": {}, "apis": [], "database": {}},
                auth_required=True
            )
        ]


global_api_designer = APIDesigner()
