"""
AIForge Sprint Task Data Model
==============================
Defines the SprintTask data model supporting the complete task lifecycle:
Pending -> Assigned -> Running -> Review -> Completed (or Failed -> Retry -> Completed).
Tracks task IDs, priorities, assigned agents, dependencies, file targets, and execution logs.
"""

import time
from typing import Dict, Any, List, Optional


class SprintTask:
    """
    Agile Sprint Task representation.
    """

    def __init__(
        self,
        task_id: str,
        description: str,
        assigned_agent: str,
        priority: str = "MEDIUM",
        estimated_time_seconds: float = 10.0,
        dependencies: Optional[List[str]] = None,
        target_files: Optional[List[str]] = None
    ) -> None:
        self.task_id = task_id
        self.description = description
        self.assigned_agent = assigned_agent
        self.priority = priority  # HIGH, MEDIUM, LOW
        self.estimated_time_seconds = estimated_time_seconds
        self.dependencies = dependencies or []
        self.target_files = target_files or []

        self.status = "Pending"  # Pending, Assigned, Running, Review, Completed, Failed, Retry
        self.retry_count = 0
        self.max_retries = 3

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_seconds: float = 0.0
        self.result_output: Optional[str] = None
        self.error_logs: List[str] = []
        self.token_usage: int = 2500
        self.llm_calls_count: int = 2

    def mark_running(self) -> None:
        self.status = "Running"
        self.start_time = time.time()

    def mark_review(self) -> None:
        self.status = "Review"

    def mark_completed(self, output: str = "Success") -> None:
        self.status = "Completed"
        self.end_time = time.time()
        if self.start_time:
            self.duration_seconds = round(self.end_time - self.start_time, 2)
        else:
            self.duration_seconds = round(self.estimated_time_seconds, 2)
        self.result_output = output

    def mark_failed(self, error_msg: str) -> None:
        self.status = "Failed"
        self.error_logs.append(error_msg)
        self.end_time = time.time()
        if self.start_time:
            self.duration_seconds = round(self.end_time - self.start_time, 2)

    def prepare_retry(self, backup_agent: Optional[str] = None) -> bool:
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = "Retry"
            if backup_agent:
                self.assigned_agent = backup_agent
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "assigned_agent": self.assigned_agent,
            "priority": self.priority,
            "estimated_time_seconds": self.estimated_time_seconds,
            "dependencies": self.dependencies,
            "target_files": self.target_files,
            "status": self.status,
            "retry_count": self.retry_count,
            "duration_seconds": self.duration_seconds,
            "result_output": self.result_output,
            "error_logs": self.error_logs,
            "token_usage": self.token_usage,
            "llm_calls_count": self.llm_calls_count
        }
