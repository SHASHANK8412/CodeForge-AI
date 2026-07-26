import io
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.project_packaging")


class ProjectPackagingAgent(BaseAgent):
    """
    Project Packaging Agent packages generated code into a clean, complete project structure
    and creates downloadable ZIP archives containing all source files, configurations, and reports.
    """

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Project Packaging Agent for AIForge. Your job is to assemble "
                "generated project artifacts, documentation, and configuration manifests into "
                "a standardized export package and create clean ZIP archives."
            ),
            task_name="project_packaging"
        )

    def generate_architecture_md(self, project_name: str, plan_dict: Dict[str, Any], arch_dict: Dict[str, Any]) -> str:
        arch_style = arch_dict.get("style", "Microservices / Modular Monolith") if isinstance(arch_dict, dict) else "Modular Architecture"
        components = arch_dict.get("components", ["Frontend", "Backend API", "Database", "Auth"]) if isinstance(arch_dict, dict) else ["Frontend", "Backend API", "Database"]

        return f"""# {project_name} - System Architecture Document

## Overview
{project_name} is built following modern production architectural guidelines with strict separation of concerns between frontend, backend, database, and container orchestration layers.

## Architectural Style
- **Pattern**: {arch_style}
- **Protocol**: RESTful HTTP / JSON
- **Frontend Stack**: React 18 + Vite + CSS
- **Backend Stack**: FastAPI (Python 3.11) + Uvicorn
- **Database Layer**: PostgreSQL / SQLite ORM

## System Component Diagram

```mermaid
graph TD
    Client[Web Browser / Client] -->|HTTP / REST| API[FastAPI Backend Engine]
    API -->|ORM / SQL| DB[(Database Storage)]
    API -->|Auth / Middleware| Auth[JWT Authentication]
    API -->|Services| BusinessLogic[Domain Services]
```

## System Components
{"".join([f"- **{c}**: Primary core system module\\n" for c in components])}
"""

    def generate_api_docs_md(self, project_name: str) -> str:
        return f"""# {project_name} - REST API Specification

## Base URL
`http://localhost:8000`

## Endpoints

### 1. System Health
- **Endpoint**: `GET /health`
- **Description**: Returns operational health status of backend & database.
- **Response**:
```json
{{
  "status": "healthy",
  "project": "{project_name}"
}}
```

### 2. Root Endpoint
- **Endpoint**: `GET /`
- **Description**: Welcomes client requests.
- **Response**:
```json
{{
  "message": "Welcome to {project_name} API"
}}
```

### 3. Core Resource Routes
- **GET /api/v1/resources**: List resources
- **POST /api/v1/resources**: Create new resource
- **GET /api/v1/resources/{{id}}**: Retrieve resource by ID
"""

    def create_zip_bytes(self, files_dict: Dict[str, str]) -> bytes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filepath, content in files_dict.items():
                zip_file.writestr(filepath, content)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
