"""
AIForge Autonomous Project Manager Agent
=========================================
Functions as an AI Engineering Manager:
1. Reads project requirements/planner output
2. Breaks projects into milestones (Setup, Auth, Frontend, Backend, Database, Testing, Deployment)
3. Divides milestones into granular tasks
4. Assigns specialized agents (Frontend, Backend, Database, QA, Reviewer, Documentation)
5. Tracks progress in real time (Progress JSON, ASCII Progress Bar, Estimated Time)
6. Detects blockers and missing dependencies
7. Auto-reassigns failed tasks for self-healing
8. Generates daily executive engineering reports
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.agents.base_agent import BaseAgent

_logger = logging.getLogger("aiforge.agents.project_manager")


class ProjectManagerAgent(BaseAgent):
    """
    Autonomous Project Manager Agent orchestrating engineering sprints.
    """

    def __init__(self, system_prompt: str = "You are the Autonomous Project Manager Agent coordinating engineering sprints.", task_name: str = "project_manager") -> None:
        super().__init__(system_prompt=system_prompt, task_name=task_name)
        self.milestones_template = [
            {"id": "m1", "title": "Milestone 1: Project Setup", "status": "Pending", "progress": 0},
            {"id": "m2", "title": "Milestone 2: Authentication & Security", "status": "Pending", "progress": 0},
            {"id": "m3", "title": "Milestone 3: Frontend User Interface", "status": "Pending", "progress": 0},
            {"id": "m4", "title": "Milestone 4: Backend API Services", "status": "Pending", "progress": 0},
            {"id": "m5", "title": "Milestone 5: Database Schemas & Models", "status": "Pending", "progress": 0},
            {"id": "m6", "title": "Milestone 6: Quality Assurance & Testing", "status": "Pending", "progress": 0},
            {"id": "m7", "title": "Milestone 7: Production Deployment", "status": "Pending", "progress": 0},
        ]

    def break_into_milestones(self, project_name: str, planner_output: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Breaks project requirements into 7 key engineering milestones."""
        milestones = []
        for template in self.milestones_template:
            m = dict(template)
            m["project_name"] = project_name
            milestones.append(m)
        _logger.info(f"ProjectManagerAgent: Decomposed '{project_name}' into {len(milestones)} milestones.")
        return milestones

    def divide_milestone_into_tasks(self, milestone_id: str, milestone_title: str) -> List[Dict[str, Any]]:
        """Divides a milestone into actionable tasks."""
        if "Authentication" in milestone_title:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "Login API Endpoint", "required_agent": "Backend Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Register API Endpoint", "required_agent": "Backend Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t3", "title": "JWT Handler & Middleware", "required_agent": "Backend Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t4", "title": "Forgot Password Endpoint", "required_agent": "Backend Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t5", "title": "Frontend Login Page Component", "required_agent": "Frontend Agent", "status": "Pending"},
            ]
        elif "Setup" in milestone_title:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "Repository Initialization", "required_agent": "DevOps Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Environment Config (.env)", "required_agent": "DevOps Agent", "status": "Pending"},
            ]
        elif "Frontend" in milestone_title:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "Dashboard UI Layout", "required_agent": "Frontend Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Navigation & Sidebar", "required_agent": "Frontend Agent", "status": "Pending"},
            ]
        elif "Backend" in milestone_title:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "REST API Controllers", "required_agent": "Backend Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Business Logic Services", "required_agent": "Backend Agent", "status": "Pending"},
            ]
        elif "Database" in milestone_title:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "SQL Schemas & ORM Models", "required_agent": "Database Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Migration Scripts", "required_agent": "Database Agent", "status": "Pending"},
            ]
        elif "Testing" in milestone_title:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "Unit & Integration Test Suite", "required_agent": "Testing Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Code Review & Quality Check", "required_agent": "Reviewer Agent", "status": "Pending"},
            ]
        else:
            return [
                {"task_id": f"{milestone_id}_t1", "title": "Docker Compose Configuration", "required_agent": "DevOps Agent", "status": "Pending"},
                {"task_id": f"{milestone_id}_t2", "title": "Deployment Verification", "required_agent": "DevOps Agent", "status": "Pending"},
            ]

    def assign_agents(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assigns specialized AI agents to pending tasks."""
        assigned = []
        for task in tasks:
            t = dict(task)
            t["assigned_at"] = time.time()
            t["status"] = "Assigned"
            assigned.append(t)
        return assigned

    def monitor_completion(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates project completion metrics."""
        total = len(tasks)
        if total == 0:
            return {"completed": 0, "remaining": 0, "progress_percentage": 0, "status": "Idle"}

        completed = len([t for t in tasks if t.get("status") in ["Completed", "Done"]])
        failed = len([t for t in tasks if t.get("status") in ["Failed", "Blocked"]])
        remaining = total - completed - failed

        pct = round((completed / total) * 100, 1)
        status = "Completed" if completed == total else ("Blocked" if failed > 0 else "Running")

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "remaining": remaining,
            "progress_percentage": pct,
            "status": status
        }

    def detect_blockers(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detects blocked tasks and missing dependencies."""
        blockers = []
        for t in tasks:
            if t.get("status") == "Failed" or t.get("error"):
                blockers.append({
                    "task_id": t["task_id"],
                    "title": t.get("title", "Task"),
                    "assigned_agent": t.get("required_agent", "Agent"),
                    "reason": t.get("error", "Dependency or execution failure"),
                    "detected_at": time.time()
                })
        return blockers

    def reassign_work(self, blocked_task: Dict[str, Any], failure_reason: str) -> Dict[str, Any]:
        """Reassigns a blocked/failed task with recovery instructions."""
        reassigned_task = dict(blocked_task)
        reassigned_task["status"] = "Reassigned"
        reassigned_task["attempts"] = reassigned_task.get("attempts", 0) + 1
        reassigned_task["recovery_note"] = f"Reassigned due to failure: {failure_reason}"
        reassigned_task["reassigned_to"] = "Backend Agent" if "API" in blocked_task.get("title", "") else "DevOps Agent"
        
        _logger.info(f"ProjectManagerAgent: Reassigned task '{blocked_task.get('title')}' -> {reassigned_task['reassigned_to']}")
        return reassigned_task

    def render_progress_bar(self, percentage: float, bar_length: int = 20) -> str:
        """Renders ASCII progress bar."""
        filled_length = int(round(bar_length * percentage / 100))
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        return f"{bar} {percentage}%"

    def generate_progress_json(self, project_name: str, tasks: List[Dict[str, Any]], current_agent: str = "Frontend") -> Dict[str, Any]:
        """Produces standard Day 29 Progress JSON."""
        metrics = self.monitor_completion(tasks)
        return {
            "project": project_name,
            "completed": metrics["completed"],
            "remaining": metrics["remaining"],
            "status": metrics["status"],
            "current_agent": current_agent,
            "progress": int(metrics["progress_percentage"]),
            "progress_bar": self.render_progress_bar(metrics["progress_percentage"])
        }

    def generate_daily_report(self, project_name: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates executive daily report."""
        completed_titles = [t["title"] for t in tasks if t.get("status") in ["Completed", "Done"]]
        running_titles = [t["title"] for t in tasks if t.get("status") in ["Running", "Assigned", "In Progress"]]
        pending_titles = [t["title"] for t in tasks if t.get("status") == "Pending"]
        
        metrics = self.monitor_completion(tasks)

        markdown_report = f"""# AIForge Daily Report - {project_name}

### Completed
{chr(10).join(['✔ ' + t for t in completed_titles]) if completed_titles else 'None yet'}

### Running
{chr(10).join(['⌛ ' + t for t in running_titles]) if running_titles else 'None'}

### Pending
{chr(10).join(['- ' + t for t in pending_titles]) if pending_titles else 'None'}

### Overall Progress
{self.render_progress_bar(metrics['progress_percentage'])}
"""
        return {
            "project_name": project_name,
            "timestamp": time.time(),
            "completed_tasks": completed_titles,
            "running_tasks": running_titles,
            "pending_tasks": pending_titles,
            "overall_progress_pct": metrics["progress_percentage"],
            "markdown": markdown_report
        }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgent execution interface."""
        prompt = inputs.get("prompt", "Software Project")
        milestones = self.break_into_milestones(prompt)
        
        all_tasks = []
        for m in milestones:
            ts = self.divide_milestone_into_tasks(m["id"], m["title"])
            all_tasks.extend(ts)

        assigned_tasks = self.assign_agents(all_tasks)
        progress_json = self.generate_progress_json(prompt, assigned_tasks)
        report = self.generate_daily_report(prompt, assigned_tasks)

        return {
            "status": "success",
            "project_name": prompt,
            "milestones": milestones,
            "tasks": assigned_tasks,
            "progress_json": progress_json,
            "daily_report": report
        }


global_project_manager_agent = ProjectManagerAgent()
