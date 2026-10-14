"""
AIForge Agent Scheduler
========================
Coordinates a shared pool of specialized AI agents across multiple concurrent projects.
Monitors agent availability and automatically schedules idle agents to pending project tasks based on priority.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.workspace.scheduler")


class AgentScheduler:
    """
    Schedules shared AI agents across projects dynamically.
    """

    def __init__(self) -> None:
        self.agents: Dict[str, Dict[str, Any]] = {
            "agent_pm": {"id": "agent_pm", "name": "Product Manager Agent", "role": "PM", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 14},
            "agent_arch": {"id": "agent_arch", "name": "Architect Agent", "role": "Architect", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 18},
            "agent_frontend": {"id": "agent_frontend", "name": "Frontend Agent", "role": "Frontend", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 25},
            "agent_backend": {"id": "agent_backend", "name": "Backend Agent", "role": "Backend", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 30},
            "agent_qa": {"id": "agent_qa", "name": "QA Agent", "role": "QA", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 20},
            "agent_devops": {"id": "agent_devops", "name": "DevOps Agent", "role": "DevOps", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 12},
            "agent_security": {"id": "agent_security", "name": "Security Agent", "role": "Security", "status": "idle", "current_project": None, "current_task": None, "tasks_completed": 10},
        }
        self.task_queue: List[Dict[str, Any]] = []
        self.execution_history: List[Dict[str, Any]] = []

    def get_agent_pool(self) -> List[Dict[str, Any]]:
        return list(self.agents.values())

    def get_idle_agents(self) -> List[Dict[str, Any]]:
        return [a for a in self.agents.values() if a["status"] == "idle"]

    def add_task_to_queue(self, project_id: str, project_name: str, task_name: str, required_role: str, priority: str = "High") -> Dict[str, Any]:
        task_id = f"task_{int(time.time() * 1000)}"
        task = {
            "task_id": task_id,
            "project_id": project_id,
            "project_name": project_name,
            "task_name": task_name,
            "required_role": required_role,
            "priority": priority,
            "status": "pending",
            "assigned_agent": None,
            "created_at": time.time()
        }
        self.task_queue.append(task)
        _logger.info(f"AgentScheduler: Task '{task_name}' added for project '{project_name}' (Priority: {priority})")
        
        # Trigger scheduling immediately
        self.schedule_next_task()
        return task

    def schedule_next_task(self) -> Optional[Dict[str, Any]]:
        if not self.task_queue:
            return None

        # Sort tasks by priority (Critical > High > Medium > Low)
        priority_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        self.task_queue.sort(key=lambda t: priority_map.get(t.get("priority", "Medium"), 1), reverse=True)

        for task in list(self.task_queue):
            if task["status"] == "pending":
                role = task["required_role"]
                # Find idle agent matching role or any idle agent if unspecified
                matching_agent = None
                for agent in self.agents.values():
                    if agent["status"] == "idle" and (agent["role"].lower() == role.lower() or role == "Any"):
                        matching_agent = agent
                        break

                if matching_agent:
                    # Assign agent to task
                    matching_agent["status"] = "busy"
                    matching_agent["current_project"] = task["project_name"]
                    matching_agent["current_task"] = task["task_name"]

                    task["status"] = "in_progress"
                    task["assigned_agent"] = matching_agent["name"]
                    task["assigned_agent_id"] = matching_agent["id"]

                    _logger.info(f"AgentScheduler: Assigned '{matching_agent['name']}' -> Task '{task['task_name']}' in Project '{task['project_name']}'")
                    return task

        return None

    def release_agent(self, agent_id: str, success: bool = True) -> Dict[str, Any]:
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            prev_task = agent.get("current_task")
            prev_project = agent.get("current_project")

            agent["status"] = "idle"
            agent["current_project"] = None
            agent["current_task"] = None
            if success:
                agent["tasks_completed"] = agent.get("tasks_completed", 0) + 1

            # Update task queue record
            for task in self.task_queue:
                if task.get("assigned_agent_id") == agent_id and task["status"] == "in_progress":
                    task["status"] = "completed" if success else "failed"
                    self.execution_history.append(task)
                    self.task_queue.remove(task)
                    break

            _logger.info(f"AgentScheduler: Agent '{agent['name']}' released (Success: {success})")
            
            # Immediately attempt to schedule next pending task
            self.schedule_next_task()

            return {"agent": agent, "completed_task": prev_task, "project": prev_project}
        raise ValueError(f"Agent ID '{agent_id}' not found.")

    def get_scheduler_status(self) -> Dict[str, Any]:
        idle_count = len(self.get_idle_agents())
        busy_count = len(self.agents) - idle_count
        return {
            "total_agents": len(self.agents),
            "idle_agents": idle_count,
            "busy_agents": busy_count,
            "pending_tasks": len([t for t in self.task_queue if t["status"] == "pending"]),
            "in_progress_tasks": len([t for t in self.task_queue if t["status"] == "in_progress"]),
            "completed_tasks": len(self.execution_history),
            "agents": list(self.agents.values()),
            "queue": self.task_queue
        }


global_agent_scheduler = AgentScheduler()
