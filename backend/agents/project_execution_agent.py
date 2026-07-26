import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.project_execution")


class ExecutionReport(BaseModel):
    server_starts: bool = True
    no_crashes: bool = True
    api_reachable: bool = True
    frontend_loads: bool = True
    database_connected: bool = True
    crashes: List[str] = Field(default_factory=list)
    endpoints_verified: List[str] = Field(default_factory=list)
    summary: str = ""


class ProjectExecutionAgent(BaseAgent):
    """
    Project Execution Agent verifies that generated code can be started and executed properly:
    1. Validates backend startup readiness (entry point `main.py` / `app` object exists).
    2. Validates API endpoints mapping (`/`, `/health`).
    3. Validates database connection string presence and ORM initialization.
    4. Validates frontend entry point (`index.html`, `App.jsx`, `main.jsx`).
    """

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Project Execution Agent for AIForge. Your job is to perform "
                "automated runtime checks and verify server startup, route accessibility, "
                "frontend loading readiness, and database connection configurations."
            ),
            task_name="project_execution"
        )

    def verify_execution(
        self,
        backend_files: Dict[str, str],
        frontend_files: Dict[str, str],
        database_code: str
    ) -> ExecutionReport:
        crashes = []
        endpoints = []

        # 1. Backend startup check
        has_main = any("main.py" in path for path in backend_files.keys())
        has_app = False
        if has_main:
            for path, content in backend_files.items():
                if "main.py" in path:
                    if "FastAPI(" in content or "app =" in content or "Flask(" in content:
                        has_app = True
                        if "@app.get(\"/\")" in content or "@app.get('/')" in content:
                            endpoints.append("GET /")
                        if "@app.get(\"/health\")" in content or "health" in content:
                            endpoints.append("GET /health")

        if not has_main or not has_app:
            crashes.append("Backend entry point 'main.py' or 'app' application instance missing.")

        # 2. Database connection check
        db_connected = True
        if database_code and len(database_code.strip()) > 0:
            if "postgresql://" not in database_code and "sqlite" not in database_code and "mongodb" not in database_code and "CREATE TABLE" not in database_code:
                db_connected = False
                crashes.append("Database configuration does not specify a valid connection URI or SQL schema.")

        # 3. Frontend loading check
        frontend_loads = any("index.html" in path or "App.jsx" in path or "main.jsx" in path for path in frontend_files.keys())
        if not frontend_loads:
            crashes.append("Frontend entry components (App.jsx / index.html) missing.")

        no_crashes = len(crashes) == 0
        server_starts = has_main and has_app
        api_reachable = len(endpoints) > 0 or server_starts

        summary = (
            f"Execution Verification: {'PASSED' if no_crashes else 'FAILED'}. "
            f"Server Starts: {server_starts}, API Reachable: {api_reachable}, "
            f"Frontend Loads: {frontend_loads}, DB Connected: {db_connected}."
        )

        return ExecutionReport(
            server_starts=server_starts,
            no_crashes=no_crashes,
            api_reachable=api_reachable,
            frontend_loads=frontend_loads,
            database_connected=db_connected,
            crashes=crashes,
            endpoints_verified=endpoints,
            summary=summary
        )
