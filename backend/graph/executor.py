import time
import logging
from typing import Dict, Any, Optional, List

from backend.graph.state import WorkflowState
from backend.graph.workflow import graph
from backend.graph.parallel import global_parallel_executor
from backend.memory.session_manager import global_session_manager, ProjectSession

logger = logging.getLogger("aiforge.graph.executor")

# Project status registry for real-time status API queries
PROJECT_STATUS_STORE: Dict[str, Dict[str, Any]] = {}


class WorkflowExecutor:
    """
    WorkflowExecutor initializes workflow state, executes the LangGraph multi-agent engine,
    handles parallel agent tasks (Frontend, Backend, Database), benchmarks execution time,
    tracks project status, and returns completed project artifacts.
    """

    def execute_project_workflow(self, prompt: str, session_id: Optional[str] = None, use_parallel: bool = True) -> WorkflowState:
        """Executes full multi-agent project workflow with optional parallel node execution."""
        start_time = time.time()
        project_id = session_id or f"proj_{int(start_time)}"

        # 1. Initialize Session & Status
        global_session_manager.create_session(project_id, prompt[:30])

        initial_state: WorkflowState = {
            "prompt": prompt,
            "session_id": project_id,
            "retrieved_context": "",
            "plan": {},
            "architecture": {},
            "frontend_code": {},
            "backend_code": {},
            "database_schema": "",
            "review": {},
            "tests": {},
            "documentation": "",
            "project_files": {},
            "errors": [],
            "retry_count": {},
            "logs": [f"Initialized Workflow for project '{project_id}'"],
            "execution_status": {
                "planner": "waiting",
                "architect": "waiting",
                "frontend": "waiting",
                "backend": "waiting",
                "database": "waiting",
                "reviewer": "waiting",
                "testing": "waiting",
                "documentation": "waiting",
                "export": "waiting"
            },
            "execution_time": {},
            "progress": 0,
            "active_agents": [],
            "is_complete": False,
            "is_cancelled": False
        }

        PROJECT_STATUS_STORE[project_id] = {
            "project_id": project_id,
            "status": "running",
            "progress": 5,
            "current_agents": ["planner"],
            "completed_agents": [],
            "logs": initial_state["logs"],
            "errors": []
        }

        # 2. Execute Planner & Architect (Sequential)
        from backend.graph.nodes import (
            planner_node, architect_node, reviewer_node,
            testing_node, documentation_node, export_node
        )

        state = planner_node(initial_state)
        PROJECT_STATUS_STORE[project_id]["progress"] = 20
        PROJECT_STATUS_STORE[project_id]["completed_agents"].append("planner")
        PROJECT_STATUS_STORE[project_id]["current_agents"] = ["architect"]

        state = architect_node(state)
        PROJECT_STATUS_STORE[project_id]["progress"] = 40
        PROJECT_STATUS_STORE[project_id]["completed_agents"].append("architect")

        # 3. Execute Coding & Database (Parallel or Sequential)
        if use_parallel:
            PROJECT_STATUS_STORE[project_id]["current_agents"] = ["frontend", "backend", "database"]
            state = global_parallel_executor.run_parallel_agents(["frontend", "backend", "database"], state)
            PROJECT_STATUS_STORE[project_id]["completed_agents"].extend(["frontend", "backend", "database"])
        else:
            from backend.graph.nodes import frontend_node, backend_node, database_node
            state = frontend_node(state)
            state = backend_node(state)
            state = database_node(state)
            PROJECT_STATUS_STORE[project_id]["completed_agents"].extend(["frontend", "backend", "database"])

        PROJECT_STATUS_STORE[project_id]["progress"] = 70

        # 4. Execute Reviewer, Testing, Documentation, Export (Sequential)
        PROJECT_STATUS_STORE[project_id]["current_agents"] = ["reviewer"]
        state = reviewer_node(state)
        PROJECT_STATUS_STORE[project_id]["completed_agents"].append("reviewer")

        PROJECT_STATUS_STORE[project_id]["current_agents"] = ["testing"]
        state = testing_node(state)
        PROJECT_STATUS_STORE[project_id]["completed_agents"].append("testing")

        PROJECT_STATUS_STORE[project_id]["current_agents"] = ["documentation"]
        state = documentation_node(state)
        PROJECT_STATUS_STORE[project_id]["completed_agents"].append("documentation")

        PROJECT_STATUS_STORE[project_id]["current_agents"] = ["export"]
        state = export_node(state)
        PROJECT_STATUS_STORE[project_id]["completed_agents"].append("export")

        elapsed = round(time.time() - start_time, 2)
        state["execution_time"]["total"] = elapsed
        state["progress"] = 100
        state["is_complete"] = True

        PROJECT_STATUS_STORE[project_id].update({
            "status": "completed",
            "progress": 100,
            "current_agents": [],
            "logs": state["logs"],
            "total_time_seconds": elapsed,
            "project_files": state["project_files"]
        })

        logger.info(f"WorkflowExecutor completed in {elapsed}s (Parallel mode: {use_parallel})")
        return state

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Returns live status, active agents, logs, and progress percentage for a project."""
        if project_id in PROJECT_STATUS_STORE:
            return PROJECT_STATUS_STORE[project_id]
        return {
            "project_id": project_id,
            "status": "unknown",
            "progress": 0,
            "current_agents": [],
            "completed_agents": [],
            "logs": [],
            "errors": ["Project ID not found in active registry."]
        }


# Global WorkflowExecutor Instance
global_workflow_executor = WorkflowExecutor()
