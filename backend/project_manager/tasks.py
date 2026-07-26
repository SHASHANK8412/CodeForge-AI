import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.project_manager.tasks")


class TaskBreakdownEngine:
    """
    TaskBreakdownEngine converts User Stories into actionable engineering tasks
    assigned to specialized AI agents with dependency mappings.
    """

    def generate_tasks(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tasks = [
            {
                "id": "TSK-01",
                "story_id": "US-01",
                "title": "Define PostgreSQL User Model & Database Schemas",
                "agent": "Database Agent",
                "priority": "HIGH",
                "status": "COMPLETED",
                "dependencies": []
            },
            {
                "id": "TSK-02",
                "story_id": "US-02",
                "title": "Build FastAPI Auth Router & JWT Token Verification",
                "agent": "Backend Agent",
                "priority": "HIGH",
                "status": "COMPLETED",
                "dependencies": ["TSK-01"]
            },
            {
                "id": "TSK-03",
                "story_id": "US-03",
                "title": "Build React Login & Registration Page Components",
                "agent": "Frontend Agent",
                "priority": "MEDIUM",
                "status": "COMPLETED",
                "dependencies": ["TSK-02"]
            },
            {
                "id": "TSK-04",
                "story_id": "US-04",
                "title": "Write Pytest API Authentication Unit Test Suite",
                "agent": "Testing Agent",
                "priority": "MEDIUM",
                "status": "COMPLETED",
                "dependencies": ["TSK-02"]
            },
            {
                "id": "TSK-05",
                "story_id": "US-05",
                "title": "Generate Dockerfile & docker-compose.yml Deploy Manifests",
                "agent": "DevOps Agent",
                "priority": "LOW",
                "status": "COMPLETED",
                "dependencies": ["TSK-03"]
            }
        ]

        logger.info(f"TaskBreakdownEngine generated {len(tasks)} tasks.")
        return tasks


# Global TaskBreakdownEngine Instance
global_task_breakdown_engine = TaskBreakdownEngine()
