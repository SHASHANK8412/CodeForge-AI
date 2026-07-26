import json
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.exporter.metadata")


class MetadataGenerator:
    """
    MetadataGenerator builds project.json metadata file with timestamp, version tag,
    agent execution metrics, and assembly telemetry.
    """

    def generate_project_metadata(
        self,
        project_name: str,
        tech_stack: Dict[str, Any],
        file_count: int,
        assembly_time_seconds: float = 0.0,
        version: str = "2.0.0"
    ) -> str:
        meta = {
            "project_name": project_name,
            "version": version,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "timestamp": time.time(),
            "frontend": tech_stack.get("frontend", "React"),
            "backend": tech_stack.get("backend", "FastAPI"),
            "database": tech_stack.get("database", "PostgreSQL"),
            "agents": [
                "Planner",
                "Architect",
                "Frontend",
                "Backend",
                "Database",
                "Reviewer",
                "Testing",
                "Documentation",
                "Exporter"
            ],
            "telemetry": {
                "file_count": file_count,
                "assembly_time_seconds": round(assembly_time_seconds, 3),
                "platform": "AIForge V2 Autonomous Engine"
            }
        }
        return json.dumps(meta, indent=2) + "\n"


# Global MetadataGenerator Instance
global_metadata_generator = MetadataGenerator()
