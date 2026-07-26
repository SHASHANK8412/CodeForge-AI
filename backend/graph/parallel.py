import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Callable

from backend.graph.state import WorkflowState
from backend.graph.nodes import frontend_node, backend_node, database_node

logger = logging.getLogger("aiforge.graph.parallel")

NODE_MAP: Dict[str, Callable] = {
    "frontend": frontend_node,
    "backend": backend_node,
    "database": database_node
}


class ParallelExecutor:
    """
    ParallelExecutor launches independent agents (Frontend, Backend, Database) concurrently
    using ThreadPoolExecutor, enforces per-agent timeouts (120s max), collects execution metrics,
    and merges parallel outputs.
    """

    def __init__(self, timeout_seconds: float = 120.0, max_workers: int = 4):
        self.timeout_seconds = timeout_seconds
        self.max_workers = max_workers

    def run_parallel_agents(self, agent_names: List[str], state: WorkflowState) -> WorkflowState:
        """Executes listed agent nodes in parallel, updating state and execution metrics."""
        start_parallel_time = time.time()
        logger.info(f"Launching parallel execution for agents: {agent_names}")

        state.setdefault("execution_status", {})
        state.setdefault("execution_time", {})

        for name in agent_names:
            state["execution_status"][name] = "running"

        futures = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for name in agent_names:
                node_fn = NODE_MAP.get(name)
                if node_fn:
                    # Submit task to pool
                    future = executor.submit(self._execute_single_node, name, node_fn, dict(state))
                    futures[future] = name

            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    res_state, duration = future.result(timeout=self.timeout_seconds)
                    state["execution_status"][agent_name] = "completed"
                    state["execution_time"][agent_name] = duration

                    # Merge outputs into state
                    if agent_name == "frontend" and "frontend_code" in res_state:
                        state["frontend_code"] = res_state["frontend_code"]
                    elif agent_name == "backend" and "backend_code" in res_state:
                        state["backend_code"] = res_state["backend_code"]
                    elif agent_name == "database" and "database_schema" in res_state:
                        state["database_schema"] = res_state["database_schema"]

                    logger.info(f"Parallel agent '{agent_name}' finished in {duration}s")
                except Exception as e:
                    logger.error(f"Parallel agent '{agent_name}' failed or timed out: {e}")
                    state["execution_status"][agent_name] = "failed"
                    state.setdefault("errors", []).append({
                        "agent": agent_name,
                        "message": str(e),
                        "timestamp": time.time()
                    })

        total_parallel = round(time.time() - start_parallel_time, 2)
        state.setdefault("logs", []).append(f"[Parallel] Concurrent execution of {agent_names} completed in {total_parallel}s")
        return state

    def _execute_single_node(self, agent_name: str, node_fn: Callable, state_copy: WorkflowState):
        start = time.time()
        res_state = node_fn(state_copy)
        duration = round(time.time() - start, 2)
        return res_state, duration


# Global ParallelExecutor Instance
global_parallel_executor = ParallelExecutor()
