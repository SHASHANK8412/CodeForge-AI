"""
AIForge V2 – System Architecture Topology Generator
===================================================
Generates High-Level & Low-Level architectural topology and component definitions.
"""

from typing import List, Dict, Any
from v2.agents.architect.models import SystemComponent


class ArchitectureTopologyGenerator:

    def generate_components(self, project_name: str, is_enterprise: bool = False) -> List[SystemComponent]:
        base_components = [
            SystemComponent(
                name="React Single Page Application",
                type="Frontend UI",
                responsibility="Renders dynamic UI views, forms, dashboards, and state components.",
                dependencies=["FastAPI Gateway"]
            ),
            SystemComponent(
                name="FastAPI REST API Gateway",
                type="API Gateway",
                responsibility="Routes client requests, enforces JWT auth, validates request payloads.",
                dependencies=["PostgreSQL Database", "Redis Cache"]
            ),
            SystemComponent(
                name="PostgreSQL Relational Persistence",
                type="Database",
                responsibility="Persists transactional user data, projects, tasks, and audit logs.",
                dependencies=[]
            ),
            SystemComponent(
                name="Redis In-Memory Cache",
                type="Cache Engine",
                responsibility="Stores session tokens, rate limiting counters, and query caches.",
                dependencies=[]
            )
        ]

        if is_enterprise:
            base_components.extend([
                SystemComponent(
                    name="ChromaDB Vector Store",
                    type="Vector Database",
                    responsibility="Stores code embeddings, documentation, and semantic knowledge items.",
                    dependencies=[]
                ),
                SystemComponent(
                    name="Docker Container Infrastructure",
                    type="Deployment Container",
                    responsibility="Orchestrates isolated services with Docker Compose.",
                    dependencies=[]
                )
            ])

        return base_components


global_architecture_generator = ArchitectureTopologyGenerator()
