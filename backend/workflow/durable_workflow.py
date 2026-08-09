"""
AIForge Temporal Durable Workflow Engine
========================================
Provides fault-tolerant, durable workflow execution with step checkpointing, activity retries, state persistence, and automatic failure recovery.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

_logger = logging.getLogger("aiforge.workflow.durable_workflow")


class DurableWorkflowEngine:
    """
    Temporal-style durable workflow orchestrator supporting checkpointing, state recovery, and automatic activity retries.
    """

    def __init__(self, state_file: Optional[Path] = None):
        _root = Path(__file__).resolve().parent.parent.parent
        self.state_file = state_file or (_root / "backend" / "workflow" / "workflow_state.json")
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self._ensure_state_file()

    def _ensure_state_file(self):
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.state_file.exists():
                self.state_file.write_text("{}", encoding="utf-8")
        except Exception as e:
            _logger.error(f"DurableWorkflowEngine: Error initializing state file: {e}")

    def start_workflow(self, workflow_id: str, prompt: str) -> Dict[str, Any]:
        """
        Initializes a durable workflow session with initial checkpoints.
        """
        state = {
            "workflow_id": workflow_id,
            "prompt": prompt,
            "status": "RUNNING",
            "checkpoints": [
                {"step": "Planning", "status": "COMPLETED", "timestamp": time.time()},
                {"step": "Architecture", "status": "COMPLETED", "timestamp": time.time()}
            ],
            "current_step": "Frontend_Backend_Generation",
            "history": [],
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        self.active_workflows[workflow_id] = state
        self._persist_workflow_state(workflow_id, state)
        _logger.info(f"DurableWorkflowEngine: Started durable workflow '{workflow_id}'")
        return state

    def execute_activity_with_retry(
        self,
        workflow_id: str,
        activity_name: str,
        activity_func: Callable[[], Any],
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Executes a workflow activity with durable retry policy and checkpointing.
        """
        wf_state = self.active_workflows.get(workflow_id) or self.start_workflow(workflow_id, "Workflow task")

        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            try:
                result = activity_func()
                # Record successful checkpoint
                checkpoint = {
                    "step": activity_name,
                    "status": "COMPLETED",
                    "attempts": attempts,
                    "timestamp": time.time()
                }
                wf_state["checkpoints"].append(checkpoint)
                wf_state["history"].append(f"Activity '{activity_name}' passed on attempt {attempts}")
                self._persist_workflow_state(workflow_id, wf_state)
                return {"status": "SUCCESS", "attempts": attempts, "result": result}
            except Exception as e:
                _logger.warning(f"DurableWorkflowEngine: Activity '{activity_name}' attempt {attempts}/{max_attempts} failed: {e}")
                if attempts >= max_attempts:
                    wf_state["status"] = "FAILED"
                    wf_state["checkpoints"].append({"step": activity_name, "status": "FAILED", "attempts": attempts})
                    self._persist_workflow_state(workflow_id, wf_state)
                    return {"status": "FAILED", "attempts": attempts, "error": str(e)}

        return {"status": "FAILED", "attempts": max_attempts, "error": "Max retries exceeded"}

    def recover_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Recovers workflow state from disk checkpoint if an interruption occurred.
        """
        try:
            if self.state_file.exists():
                content = json.loads(self.state_file.read_text(encoding="utf-8"))
                if workflow_id in content:
                    recovered = content[workflow_id]
                    recovered["status"] = "RECOVERED_AND_RUNNING"
                    self.active_workflows[workflow_id] = recovered
                    _logger.info(f"DurableWorkflowEngine: Recovered workflow '{workflow_id}' from checkpoint.")
                    return recovered
        except Exception as e:
            _logger.error(f"DurableWorkflowEngine: Error recovering workflow: {e}")

        return self.start_workflow(workflow_id, "Recovered workflow")

    def _persist_workflow_state(self, workflow_id: str, state: Dict[str, Any]):
        try:
            data = {}
            if self.state_file.exists():
                txt = self.state_file.read_text(encoding="utf-8")
                data = json.loads(txt) if txt.strip() else {}
            data[workflow_id] = state
            self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"DurableWorkflowEngine: Error persisting state: {e}")


global_durable_workflow = DurableWorkflowEngine()
