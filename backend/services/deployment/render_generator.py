import logging
from typing import List

_logger = logging.getLogger("aiforge.performance")

class RenderGenerator:
    """
    Generates render.yaml for Render Blueprint deployments, auto-wiring web services,
    databases, and startup commands.
    """

    def __init__(self) -> None:
        pass

    def generate_config(
        self,
        app_name: str,
        databases: List[str],
        backend_framework: str = "fastapi",
        backend_port: int = 8000
    ) -> str:
        """
        Generates Render blueprint render.yaml structure.
        """
        _logger.info(f"Generating render.yaml configuration for app: {app_name}")
        
        has_postgres = "postgres" in [db.lower() for db in databases]
        
        yaml_content = f"""services:
  # FastAPI backend service
  - type: web
    name: {app_name}-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port {backend_port}
    envVars:
      - key: PORT
        value: "{backend_port}"
"""

        if has_postgres:
            yaml_content += f"""      - key: DATABASE_URL
        fromDatabase:
          name: {app_name}-db
          property: connectionString
"""

        if has_postgres:
            yaml_content += f"""
databases:
  - name: {app_name}-db
    databaseName: aiforge_db
    user: postgres
"""

        return yaml_content
