"""
AIForge Day 27 — Centralized DatabaseService
============================================
Unified database management service handling structured application entities,
pgvector vector store coordination, Engineering Memory persistence, and health status reporting.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.database.connection import check_db_health, SessionLocal, engine, Base
from backend.database.models import (
    UserModel, ProjectModel, AgentModel, RunModel, IncidentModel,
    DeploymentModel, ArchitectureDecisionModel, EngineeringMemoryModel, VectorEmbeddingModel
)
from backend.database.vector import get_vector_store, VectorStore
from backend.database.repositories.memory_repository import global_postgres_memory_repository

_logger = logging.getLogger("aiforge.database.service")


class DatabaseService:
    """
    Centralized service for PostgreSQL & pgvector Database Layer.
    """

    def __init__(self, provider: str = "postgres"):
        self.provider = provider
        self.vector_store: VectorStore = get_vector_store(provider)

    def initialize(self):
        """Initializes tables if using SQLite fallback; Alembic manages PostgreSQL."""
        try:
            Base.metadata.create_all(bind=engine)
            _logger.info("[DatabaseService] Database metadata initialized.")
        except Exception as e:
            _logger.warning(f"[DatabaseService] Table init notice: {e}")

    def get_health(self) -> Dict[str, Any]:
        return check_db_health()

    def save_project(self, project_id: str, name: str, description: str = "") -> ProjectModel:
        db = SessionLocal()
        try:
            p = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
            if not p:
                p = ProjectModel(id=project_id, name=name, description=description)
                db.add(p)
            else:
                p.name = name
                p.description = description
            db.commit()
            db.refresh(p)
            return p
        finally:
            db.close()

    def get_project(self, project_id: str) -> Optional[ProjectModel]:
        db = SessionLocal()
        try:
            return db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        finally:
            db.close()


global_database_service = DatabaseService()
