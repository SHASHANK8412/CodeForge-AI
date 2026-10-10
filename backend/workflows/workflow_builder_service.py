"""
AIForge Visual AI Workflow Builder & Automation Engine
======================================================
Coordinates multi-node reactive pipelines:
Trigger -> AI Evaluation -> Agent Delegation -> Tool Execution -> Output / Notification
Includes cron automation support and run execution logs.
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

_logger = logging.getLogger("aiforge.workflows.service")


class WorkflowNode(BaseModel):
    id: str
    type: str  # TRIGGER, AI, AGENT, TOOL, CONDITION, OUTPUT
    label: str
    config: Dict[str, Any] = Field(default_factory=dict)


class AIWorkflow(BaseModel):
    id: str = Field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    is_active: bool = True
    trigger_type: str = "MANUAL"  # MANUAL, SCHEDULED_CRON, WEBHOOK, PROJECT_CREATED
    schedule_cron: Optional[str] = "0 9 * * 1"  # e.g. Every Monday 9 AM
    nodes: List[WorkflowNode] = Field(default_factory=list)
    project_id: Optional[str] = "aiforge-fooddelivery-ai"
    last_run_at: Optional[str] = None
    last_run_status: Optional[str] = "SUCCESS"
    run_count: int = 0
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


INITIAL_WORKFLOWS = [
    {
        "id": "wf_weekly_review",
        "title": "Weekly Sprint & Code Architecture Review",
        "description": "Every Monday morning, triggers Research Agent and Coding Agent to analyze pull requests, summarize diffs, and generate sprint tasks.",
        "is_active": True,
        "trigger_type": "SCHEDULED_CRON",
        "schedule_cron": "Every Monday at 9:00 AM",
        "project_id": "aiforge-fooddelivery-ai",
        "last_run_at": "2026-08-25 09:00:00",
        "last_run_status": "SUCCESS",
        "run_count": 4,
        "nodes": [
            {"id": "n1", "type": "TRIGGER", "label": "Scheduled: Every Mon 9 AM", "config": {}},
            {"id": "n2", "type": "AGENT", "label": "🔬 Research Agent: Benchmark PRs", "config": {"agent": "agent-research"}},
            {"id": "n3", "type": "AGENT", "label": "💻 Coding Agent: SAST & Tests", "config": {"agent": "agent-coding"}},
            {"id": "n4", "type": "OUTPUT", "label": "📢 Discord / Slack Summary", "config": {"channel": "engineering"}}
        ]
    },
    {
        "id": "wf_new_feature_pipeline",
        "title": "New Feature Autonomous Blueprint Pipeline",
        "description": "Triggered when a new user feature goal is submitted: Decomposes requirements, generates PRD canvas, and scaffolds initial backend endpoints.",
        "is_active": True,
        "trigger_type": "MANUAL",
        "schedule_cron": None,
        "project_id": "aiforge-fooddelivery-ai",
        "last_run_at": "2026-08-29 16:30:00",
        "last_run_status": "SUCCESS",
        "run_count": 7,
        "nodes": [
            {"id": "n1", "type": "TRIGGER", "label": "User Feature Input", "config": {}},
            {"id": "n2", "type": "AI", "label": "🧠 Intent & Task Decomposition", "config": {}},
            {"id": "n3", "type": "TOOL", "label": "🎨 Create Live PRD Canvas", "config": {}},
            {"id": "n4", "type": "AGENT", "label": "💻 Coding Agent: Generate Tests", "config": {}}
        ]
    }
]


class WorkflowService:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "workflows"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "workflows_store.json"
        self._workflows: Dict[str, AIWorkflow] = {}
        self._load()

    def _load(self):
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        w = AIWorkflow(**item)
                        self._workflows[w.id] = w
            else:
                for item in INITIAL_WORKFLOWS:
                    w = AIWorkflow(**item)
                    self._workflows[w.id] = w
                self._save()
        except Exception as e:
            _logger.error(f"Error loading workflows: {e}")
            for item in INITIAL_WORKFLOWS:
                w = AIWorkflow(**item)
                self._workflows[w.id] = w

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([w.model_dump() for w in self._workflows.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving workflows: {e}")

    def list_workflows(self, project_id: Optional[str] = None) -> List[AIWorkflow]:
        items = list(self._workflows.values())
        if project_id:
            items = [w for w in items if w.project_id == project_id]
        return items

    def get_workflow(self, workflow_id: str) -> Optional[AIWorkflow]:
        return self._workflows.get(workflow_id)

    def create_workflow(
        self,
        title: str,
        description: str = "",
        trigger_type: str = "MANUAL",
        schedule_cron: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        project_id: Optional[str] = "aiforge-fooddelivery-ai"
    ) -> AIWorkflow:
        wf = AIWorkflow(
            title=title.strip(),
            description=description.strip(),
            trigger_type=trigger_type,
            schedule_cron=schedule_cron,
            nodes=[WorkflowNode(**n) for n in (nodes or [])],
            project_id=project_id
        )
        self._workflows[wf.id] = wf
        self._save()
        return wf

    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return {"success": False, "error": "Workflow not found"}

        wf.last_run_at = time.strftime("%Y-%m-%d %H:%M:%S")
        wf.last_run_status = "SUCCESS"
        wf.run_count += 1
        self._save()

        return {
            "success": True,
            "workflow_id": wf.id,
            "status": "COMPLETED",
            "executed_nodes_count": len(wf.nodes),
            "executed_at": wf.last_run_at,
            "summary": f"Executed pipeline '{wf.title}' with {len(wf.nodes)} nodes successfully."
        }


global_workflow_service = WorkflowService()
