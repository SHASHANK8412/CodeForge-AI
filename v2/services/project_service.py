"""
AIForge V2 – Persistent Project Service
=======================================
Service layer managing project lifecycles, full-stack workflow orchestrations, and database persistence.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from v2.database.db import SessionLocal
from v2.database.crud import create_project, get_project, list_projects, update_project, delete_project
from v2.database.schemas_memory import ProjectCreateSchema
from v2.services.memory_service import global_memory_service

_logger = logging.getLogger("aiforge.v2.services.project")


class ProjectService:
    """
    Project Service managing CRUD lifecycles and autonomous workflow memory integration.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _get_db_session(self) -> Session:
        return self.db if self.db is not None else SessionLocal()

    def create_new_project(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        db = self._get_db_session()
        try:
            schema = ProjectCreateSchema(title=title, description=description)
            project = create_project(db, schema)
            _logger.info(f"ProjectService: Created project ID {project.id} ('{title}')")

            # Record initial user conversation
            global_memory_service.record_conversation(project.id, "user", f"Create project '{title}': {description or ''}")

            return {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at
            }
        finally:
            if self.db is None:
                db.close()

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        db = self._get_db_session()
        try:
            project = get_project(db, project_id)
            if not project:
                return None
            return {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at,
                "tasks_count": len(project.tasks) if project.tasks else 0,
                "conversations_count": len(project.conversations) if project.conversations else 0
            }
        finally:
            if self.db is None:
                db.close()

    def fetch_all_projects(self) -> List[Dict[str, Any]]:
        db = self._get_db_session()
        try:
            projects = list_projects(db)
            return [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "status": p.status,
                    "created_at": p.created_at
                }
                for p in projects
            ]
        finally:
            if self.db is None:
                db.close()

    def update_existing_project(self, project_id: str, title: Optional[str] = None, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        db = self._get_db_session()
        try:
            p = update_project(db, project_id, title=title, status=status)
            if not p:
                return None
            return {"id": p.id, "title": p.title, "status": p.status}
        finally:
            if self.db is None:
                db.close()

    def remove_project(self, project_id: str) -> bool:
        db = self._get_db_session()
        try:
            return delete_project(db, project_id)
        finally:
            if self.db is None:
                db.close()


global_project_service = ProjectService()
