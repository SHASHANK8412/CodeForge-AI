"""
AIForge Autonomous Project Manager
===================================
The central orchestrator that decomposes projects into milestones, phases, tasks,
and dependency graphs. It assigns work to agents, predicts ETAs, tracks progress,
detects blockers, re-plans automatically, and produces executive reports.

Acts as a world-class Technical Program Manager for an autonomous engineering org.
"""
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.project_manager.state_engine import ProjectStateEngine
from backend.project_manager.sprint_planner import SprintPlanner
from backend.project_manager.dependency_graph import DependencyGraph
from backend.project_manager.task_scheduler import TaskScheduler
from backend.project_manager.progress_tracker import ProgressTracker
from backend.project_manager.resume_engine import ResumeEngine
from backend.project_manager.bug_backlog import BugBacklog
from backend.project_manager.milestone_generator import MilestoneGenerator
from backend.project_manager.decision_store import DecisionStore
from backend.project_manager.standup_generator import StandupGenerator

_logger = logging.getLogger("aiforge.project_manager")

# ---------------------------------------------------------
# Agent-level execution time estimates (seconds)
# ---------------------------------------------------------
_AGENT_ETA = {
    "planner":       8,
    "architect":     12,
    "database":      15,
    "backend":       25,
    "frontend":      30,
    "testing":       18,
    "reviewer":      10,
    "deployment":    20,
    "documentation": 12,
}

# ---------------------------------------------------------
# Phase templates used to decompose any project
# ---------------------------------------------------------
_PHASE_TEMPLATES = [
    {"phase": "Planning",       "tasks": ["planner", "architect"]},
    {"phase": "Infrastructure", "tasks": ["database"]},
    {"phase": "Core Build",     "tasks": ["backend", "frontend"]},
    {"phase": "Quality",        "tasks": ["testing", "reviewer"]},
    {"phase": "Release",        "tasks": ["deployment", "documentation"]},
]


class AutonomousProjectManager:
    """
    Orchestrates the entire project lifecycle autonomously.

    Capabilities
    ------------
    * Decomposes a project prompt into milestones, phases, and tasks
    * Builds a dependency graph and calculates execution order
    * Schedules agents with maximum parallelism respecting deps
    * Predicts end-to-end ETA using historical execution metrics
    * Tracks real-time progress and detects blockers
    * Re-plans automatically when tasks fail or block
    * Resumes interrupted work from persistent project_state.json
    * Produces daily standups, sprint summaries, and executive reports
    * Never repeats completed work
    """

    def __init__(self, state_file: str = None) -> None:
        self.state_engine = ProjectStateEngine(state_file=state_file)
        self.sprint_planner = SprintPlanner()
        self.dep_graph = DependencyGraph()
        self.task_scheduler = TaskScheduler()
        self.progress_tracker = ProgressTracker()
        self.resume_engine = ResumeEngine()
        self.bug_backlog = BugBacklog()
        self.milestone_gen = MilestoneGenerator()
        self.decision_store = DecisionStore()
        self.standup_gen = StandupGenerator()
        self._execution_log: List[Dict[str, Any]] = []

    # ===========================================================
    # 1. PROJECT ROADMAP
    # ===========================================================
    def generate_roadmap(self, prompt: str) -> Dict[str, Any]:
        """
        Given a natural-language project prompt, produce a complete
        project roadmap including milestones, phases, tasks, deps,
        agent assignments, sprints, ETA, and risk analysis.
        """
        start_ts = time.perf_counter()
        project_name = prompt.strip()[:80]

        # --- milestones ---
        milestones = self._generate_milestones(project_name)

        # --- phases & tasks ---
        phases = self._decompose_into_phases()

        # --- dependency graph ---
        dep_order = self.dep_graph.get_execution_order()

        # --- agent assignments ---
        assignments = self.task_scheduler.schedule_tasks(dep_order)

        # --- parallel schedule (layers of independent tasks) ---
        parallel_plan = self._compute_parallel_schedule(dep_order)

        # --- sprint plan ---
        sprints = self.sprint_planner.generate_sprints(dep_order)

        # --- ETA ---
        eta = self._predict_eta(dep_order)

        # --- risk analysis ---
        risks = self._analyse_risks(dep_order)

        # --- persist initial state ---
        self._init_project_state(project_name, dep_order)

        # --- recovery plan ---
        recovery = self._build_recovery_plan()

        elapsed = round(time.perf_counter() - start_ts, 3)

        roadmap = {
            "project_name": project_name,
            "generated_at": datetime.utcnow().isoformat(),
            "planning_duration_s": elapsed,
            "milestones": milestones,
            "phases": phases,
            "dependency_order": dep_order,
            "parallel_schedule": parallel_plan,
            "agent_assignments": assignments,
            "sprint_plan": sprints,
            "eta": eta,
            "risk_analysis": risks,
            "recovery_plan": recovery,
            "progress": self._get_progress_snapshot(),
            "execution_queue": dep_order,
        }
        _logger.info(f"Roadmap generated for '{project_name}' in {elapsed}s")
        return roadmap

    # ===========================================================
    # 2. MILESTONES
    # ===========================================================
    def _generate_milestones(self, project_name: str) -> List[Dict[str, Any]]:
        base = self.milestone_gen.generate_milestones([])
        milestones = [
            {"id": "M0", "title": "Project Kickoff",
             "description": f"Initialise '{project_name}' plan and architecture.", "status": "Done"},
        ]
        for m in base:
            m["status"] = "Planned"
            milestones.append(m)
        milestones.append({
            "id": f"M{len(milestones)}",
            "title": "Deployment & Handoff",
            "description": "Ship production artefacts and documentation.",
            "status": "Planned",
        })
        return milestones

    # ===========================================================
    # 3. PHASES & TASK DECOMPOSITION
    # ===========================================================
    def _decompose_into_phases(self) -> List[Dict[str, Any]]:
        phases = []
        for tmpl in _PHASE_TEMPLATES:
            phases.append({
                "phase": tmpl["phase"],
                "tasks": tmpl["tasks"],
                "status": "Pending",
            })
        return phases

    # ===========================================================
    # 4. PARALLEL SCHEDULE
    # ===========================================================
    def _compute_parallel_schedule(self, ordered: List[str]) -> List[Dict[str, Any]]:
        """
        Compute execution layers: tasks whose dependencies are all
        satisfied can run in parallel within the same layer.
        """
        completed: set = set()
        layers: List[Dict[str, Any]] = []
        remaining = list(ordered)

        while remaining:
            layer_tasks = []
            for task in remaining:
                deps = self.dep_graph.dependencies.get(task, [])
                if all(d in completed for d in deps):
                    layer_tasks.append(task)
            if not layer_tasks:
                # Prevent infinite loop – schedule everything left
                layer_tasks = remaining[:]
            for t in layer_tasks:
                remaining.remove(t)
                completed.add(t)
            layers.append({
                "layer": len(layers) + 1,
                "parallel_tasks": layer_tasks,
                "agents": [self.task_scheduler.agent_map.get(t, "GeneralAgent") for t in layer_tasks],
            })
        return layers

    # ===========================================================
    # 5. ETA PREDICTION
    # ===========================================================
    def _predict_eta(self, ordered: List[str]) -> Dict[str, Any]:
        """
        Predicts execution time using the parallel schedule (critical-
        path analysis: each layer's duration is its slowest task).
        """
        layers = self._compute_parallel_schedule(ordered)
        layer_times = []
        for layer in layers:
            slowest = max(
                _AGENT_ETA.get(t, 10) for t in layer["parallel_tasks"]
            )
            layer_times.append(slowest)

        sequential_total = sum(_AGENT_ETA.get(t, 10) for t in ordered)
        parallel_total = sum(layer_times)

        return {
            "sequential_estimate_s": sequential_total,
            "parallel_estimate_s": parallel_total,
            "speedup_factor": round(sequential_total / max(parallel_total, 1), 2),
            "layer_breakdown": [
                {"layer": i + 1, "duration_s": lt}
                for i, lt in enumerate(layer_times)
            ],
        }

    # ===========================================================
    # 6. RISK ANALYSIS
    # ===========================================================
    def _analyse_risks(self, ordered: List[str]) -> List[Dict[str, Any]]:
        risks: List[Dict[str, Any]] = []

        # Long-running tasks
        for task in ordered:
            eta = _AGENT_ETA.get(task, 10)
            if eta >= 25:
                risks.append({
                    "risk": f"'{task}' has high estimated duration ({eta}s)",
                    "severity": "Medium",
                    "mitigation": "Monitor execution; apply parallelism where possible.",
                })

        # Tasks with many dependants (bottleneck risk)
        for task in ordered:
            dependants = [
                t for t, deps in self.dep_graph.dependencies.items()
                if task in deps
            ]
            if len(dependants) >= 2:
                risks.append({
                    "risk": f"'{task}' is a bottleneck ({len(dependants)} tasks depend on it)",
                    "severity": "High",
                    "mitigation": "Prioritise this task; allocate extra resources.",
                })

        if not risks:
            risks.append({
                "risk": "No significant risks detected.",
                "severity": "Low",
                "mitigation": "Continue with planned schedule.",
            })

        return risks

    # ===========================================================
    # 7. PROGRESS TRACKING
    # ===========================================================
    def _get_progress_snapshot(self) -> Dict[str, Any]:
        state = self.state_engine.load_state()
        tasks = state.get("tasks", {})
        total = len(tasks) if tasks else 0
        completed = sum(1 for t in tasks.values() if t.get("status") == "Completed")
        in_progress = sum(1 for t in tasks.values() if t.get("status") == "In Progress")
        pending = sum(1 for t in tasks.values() if t.get("status") == "Pending")
        blocked = sum(1 for t in tasks.values() if t.get("status") == "Blocked")
        failed = sum(1 for t in tasks.values() if t.get("status") == "Failed")

        pct = round((completed / total) * 100.0, 1) if total else 0.0

        return {
            "completion_percentage": pct,
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "blocked": blocked,
            "failed": failed,
        }

    # ===========================================================
    # 8. BLOCKER DETECTION + AUTO RE-PLAN
    # ===========================================================
    def detect_and_replan(self) -> Dict[str, Any]:
        """
        Scans project state for blocked/failed tasks and builds a
        re-plan that skips completed work and reschedules the rest.
        """
        state = self.state_engine.load_state()
        tasks = state.get("tasks", {})

        blockers = [n for n, t in tasks.items() if t.get("status") in ("Blocked", "Failed")]
        if not blockers:
            return {"blockers": [], "action": "No re-plan needed. All tasks healthy."}

        # Re-plan: reset blocked tasks to Pending, schedule them next
        for b in blockers:
            self.state_engine.update_task(b, "Pending", "Auto-replanned after blocker detected")

        remaining = self.resume_engine.get_incomplete_tasks(self.state_engine.load_state())
        new_schedule = self.task_scheduler.schedule_tasks(remaining)

        return {
            "blockers": blockers,
            "action": "Replanned",
            "new_schedule": new_schedule,
        }

    # ===========================================================
    # 9. RESUME INTERRUPTED WORK
    # ===========================================================
    def resume(self) -> Dict[str, Any]:
        state = self.state_engine.load_state()
        incomplete = self.resume_engine.get_incomplete_tasks(state)

        if not incomplete:
            return {
                "status": "All tasks completed. Nothing to resume.",
                "progress": self._get_progress_snapshot(),
            }

        next_task = incomplete[0]
        agent = self.task_scheduler.agent_map.get(next_task.lower(), "GeneralAgent")

        return {
            "status": "Resuming",
            "next_task": next_task,
            "assigned_agent": agent,
            "remaining_tasks": incomplete,
            "progress": self._get_progress_snapshot(),
        }

    # ===========================================================
    # 10. RECOVERY PLAN
    # ===========================================================
    def _build_recovery_plan(self) -> Dict[str, Any]:
        return {
            "strategy": "On failure: auto-retry up to 3 times, then escalate to Reviewer Agent.",
            "max_retries": 3,
            "fallback_agent": "ReviewerAgent",
            "persist_state": True,
            "resume_on_restart": True,
        }

    # ===========================================================
    # 11. DAILY REPORT
    # ===========================================================
    def generate_daily_report(self) -> Dict[str, Any]:
        state = self.state_engine.load_state()
        standup = self.standup_gen.generate_standup_report(state)
        progress = self._get_progress_snapshot()
        bugs = self.bug_backlog.get_open_bugs()
        decisions = self.decision_store.get_decisions()

        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "standup": standup,
            "progress": progress,
            "open_bugs": len(bugs),
            "architecture_decisions": len(decisions),
        }

    # ===========================================================
    # 12. MARK TASK COMPLETE (for agents to call)
    # ===========================================================
    def complete_task(self, task_name: str, details: str = "") -> Dict[str, Any]:
        self.state_engine.update_task(task_name, "Completed", details)
        progress = self._get_progress_snapshot()
        return {
            "task": task_name,
            "status": "Completed",
            "progress": progress,
        }

    def start_task(self, task_name: str) -> None:
        self.state_engine.update_task(task_name, "In Progress")

    def block_task(self, task_name: str, reason: str = "") -> None:
        self.state_engine.update_task(task_name, "Blocked", reason)

    def fail_task(self, task_name: str, reason: str = "") -> None:
        self.state_engine.update_task(task_name, "Failed", reason)

    # ===========================================================
    # HELPERS
    # ===========================================================
    def _init_project_state(self, project_name: str, tasks: List[str]) -> None:
        """Initialise state only for tasks that are not yet tracked."""
        state = self.state_engine.load_state()
        state["project_name"] = project_name
        state["status"] = "Active"
        existing = state.setdefault("tasks", {})
        for t in tasks:
            if t not in existing:
                existing[t] = {"status": "Pending", "details": ""}
        self.state_engine.save_state(state)
