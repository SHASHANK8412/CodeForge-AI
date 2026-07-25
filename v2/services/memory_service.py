"""
AIForge V2 – Persistent Memory Service
======================================
High-level service managing project memory, agent telemetry persistence, and conversation history retrieval.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from v2.database.db import SessionLocal
from v2.database.crud import (
    create_conversation, get_conversation_history,
    create_task, create_agent_log, list_logs_by_project,
    get_project
)
from v2.database.schemas_memory import (
    ConversationCreateSchema, TaskCreateSchema, AgentLogCreateSchema
)

_logger = logging.getLogger("aiforge.v2.services.memory")


class MemoryService:
    """
    Service layer providing memory storage and retrieval for AIForge V2.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _get_db_session(self) -> Session:
        return self.db if self.db is not None else SessionLocal()

    def record_conversation(self, project_id: str, role: str, message: str) -> None:
        db = self._get_db_session()
        try:
            schema = ConversationCreateSchema(project_id=project_id, role=role, message=message)
            create_conversation(db, schema)
            _logger.info(f"MemoryService: Recorded conversation [{role}] for project {project_id}")
        finally:
            if self.db is None:
                db.close()

    def record_agent_output(self, project_id: str, agent_name: str, prompt: str, output: str, duration_ms: float = 0.0) -> None:
        db = self._get_db_session()
        try:
            # Record Task
            task_schema = TaskCreateSchema(
                project_id=project_id,
                agent=agent_name,
                prompt=prompt,
                result=output,
                execution_time=duration_ms
            )
            create_task(db, task_schema)

            # Record Agent Log
            log_schema = AgentLogCreateSchema(
                project_id=project_id,
                agent=agent_name,
                input=prompt,
                output=output,
                duration=duration_ms,
                success=True
            )
            create_agent_log(db, log_schema)
            _logger.info(f"MemoryService: Recorded output for agent '{agent_name}' in project {project_id}")
        finally:
            if self.db is None:
                db.close()

    def get_project_memory(self, project_id: str) -> Dict[str, Any]:
        db = self._get_db_session()
        try:
            project = get_project(db, project_id)
            conversations = get_conversation_history(db, project_id)
            logs = list_logs_by_project(db, project_id)

            return {
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "description": project.description,
                    "status": project.status
                } if project else None,
                "conversations_count": len(conversations),
                "conversations": [
                    {"id": c.id, "role": c.role, "message": c.message, "created_at": c.created_at}
                    for c in conversations
                ],
                "logs_count": len(logs),
                "logs": [
                    {"id": l.id, "agent": l.agent, "duration": l.duration, "timestamp": l.timestamp}
                    for l in logs
                ]
            }
        finally:
            if self.db is None:
                db.close()


global_memory_service = MemoryService()
