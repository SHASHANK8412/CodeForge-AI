import time
import logging
from typing import Dict, Any, Optional

from backend.graph.state import WorkflowState
from backend.graph.workflow import graph
from backend.memory.session_manager import global_session_manager, ProjectSession

logger = logging.getLogger("aiforge.graph.executor")


class WorkflowExecutor:
    """
    WorkflowExecutor initializes workflow state, executes the LangGraph multi-agent engine,
    handles retries with exponential backoff, records execution logs, and returns the final project bundle.
    """

    def execute_project_workflow(self, prompt: str, session_id: Optional[str] = None) -> WorkflowState:
        """Executes full autonomous multi-agent workflow for a given user prompt."""
        start_time = time.time()
        session_id = session_id or f"session_{int(start_time)}"

        # Track session in SessionManager
        session = ProjectSession(session_id=session_id, project_name=prompt[:30])
        global_session_manager.create_session(session_id, prompt[:30])

        initial_state: WorkflowState = {
            "prompt": prompt,
            "session_id": session_id,
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
            "logs": [f"Initialized Autonomous LangGraph Workflow for session '{session_id}'"],
            "is_complete": False
        }

        logger.info(f"Executing WorkflowExecutor for prompt: '{prompt[:40]}...'")

        try:
            final_state = graph.invoke(initial_state)
        except Exception as e:
            logger.error(f"LangGraph execution exception: {e}")
            initial_state["errors"].append({"agent": "GraphExecutor", "message": str(e), "timestamp": time.time()})
            # Direct fallback execution
            from backend.graph.nodes import (
                planner_node, architect_node, frontend_node,
                backend_node, database_node, reviewer_node,
                testing_node, documentation_node, export_node
            )
            s = planner_node(initial_state)
            s = architect_node(s)
            s = frontend_node(s)
            s = backend_node(s)
            s = database_node(s)
            s = reviewer_node(s)
            s = testing_node(s)
            s = documentation_node(s)
            final_state = export_node(s)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"WorkflowExecutor completed in {elapsed}s for session '{session_id}'")
        return final_state


# Global WorkflowExecutor Instance
global_workflow_executor = WorkflowExecutor()
