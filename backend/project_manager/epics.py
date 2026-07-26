import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.project_manager.epics")


class EpicGenerator:
    """
    EpicGenerator breaks down high-level project requirements into structured Epics.
    """

    def generate_epics(self, prompt: str) -> List[Dict[str, Any]]:
        epics = [
            {
                "id": "EP-01",
                "title": "Authentication & Authorization",
                "description": "User registration, OAuth2 JWT login, and role-based access control."
            },
            {
                "id": "EP-02",
                "title": "Core Domain Services & APIs",
                "description": "Backend business logic, CRUD endpoints, and service layer."
            },
            {
                "id": "EP-03",
                "title": "Database Schema & Persistence Layer",
                "description": "PostgreSQL models, async database sessions, and migrations."
            },
            {
                "id": "EP-04",
                "title": "Frontend Web Application UI",
                "description": "React single-page application dashboard and components."
            },
            {
                "id": "EP-05",
                "title": "DevOps & Containerized Deployment",
                "description": "Dockerfile, Docker Compose, Nginx reverse proxy, and CI/CD pipelines."
            }
        ]

        logger.info(f"EpicGenerator generated {len(epics)} epics for '{prompt[:30]}'")
        return epics


# Global EpicGenerator Instance
global_epic_generator = EpicGenerator()
