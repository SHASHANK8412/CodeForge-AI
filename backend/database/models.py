"""
AIForge Day 27 — SQLAlchemy Database Models
============================================
Defines structured application data models for Users, Projects, Agents, Runs,
Incidents, Deployments, Architecture Decisions, Engineering Memories, and Vector Embeddings.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.database.connection import Base

# Try importing pgvector Vector type
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(64), default="DEVELOPER")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(64), default=lambda: datetime.now().isoformat())


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")
    status = Column(String(64), default="ACTIVE", index=True)
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(64), default=lambda: datetime.now().isoformat())


class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    name = Column(String(128), nullable=False)
    type = Column(String(64), nullable=False)
    status = Column(String(64), default="IDLE")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())


class RunModel(Base):
    __tablename__ = "runs"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    status = Column(String(64), default="SUCCESS")
    duration_s = Column(Float, default=0.0)
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    type = Column(String(64), nullable=False, index=True)
    severity = Column(String(64), default="HIGH")
    status = Column(String(64), default="INVESTIGATING", index=True)
    symptoms = Column(Text, default="[]")
    root_cause = Column(Text, default="")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())


class DeploymentModel(Base):
    __tablename__ = "deployments"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    environment = Column(String(64), default="staging")
    status = Column(String(64), default="SUCCESS", index=True)
    commit_hash = Column(String(64), default="head")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())


class ArchitectureDecisionModel(Base):
    __tablename__ = "architecture_decisions"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(64), default="ACCEPTED", index=True)
    decision = Column(Text, nullable=False)
    tradeoffs = Column(Text, default="")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())


class EngineeringMemoryModel(Base):
    __tablename__ = "engineering_memories"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    type = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    importance = Column(String(64), default="HIGH", index=True)
    confidence = Column(String(64), default="HIGH")
    source = Column(String(64), default="DEBATE")
    status = Column(String(64), default="ACTIVE", index=True)
    version = Column(Integer, default=1)
    tags_json = Column(Text, default="[]")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat(), index=True)
    updated_at = Column(String(64), default=lambda: datetime.now().isoformat())


class VectorEmbeddingModel(Base):
    __tablename__ = "vector_embeddings"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    collection_name = Column(String(128), default="aiforge_knowledge", index=True)
    document_id = Column(String(128), index=True, nullable=False)
    text = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    embedding_json = Column(Text, nullable=False)  # JSON representation of float list
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())

    __table_args__ = (
        Index("idx_vec_proj_coll", "project_id", "collection_name"),
        Index("idx_vec_doc_id", "project_id", "document_id"),
    )


class WorkflowSessionModel(Base):
    __tablename__ = "workflow_sessions"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    thread_id = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(64), default="WAITING_FOR_APPROVAL", index=True)
    current_agent = Column(String(64), default="architect")
    approval_status = Column(String(64), default="PENDING", index=True)
    approval_stage = Column(String(64), default="ARCHITECTURE")
    user_feedback = Column(Text, default="")
    workflow_state_json = Column(Text, default="{}")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(64), default=lambda: datetime.now().isoformat())


class WorkflowCheckpointModel(Base):
    __tablename__ = "workflow_checkpoints"

    id = Column(String(64), primary_key=True, index=True)
    thread_id = Column(String(64), index=True, nullable=False)
    checkpoint_id = Column(String(64), index=True, nullable=False)
    parent_id = Column(String(64), nullable=True)
    checkpoint_data = Column(Text, nullable=False)
    metadata_data = Column(Text, nullable=False)
    created_at = Column(String(64), default=lambda: datetime.now().isoformat(), index=True)


class ProjectMemoryItemModel(Base):
    __tablename__ = "project_memory_items"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    memory_type = Column(String(64), index=True, nullable=False)  # REQUIREMENT, ARCHITECTURE, DECISION, CONVENTION, ERROR, FIX, USER_PREFERENCE, DEPENDENCY, API, DATABASE
    key = Column(String(255), index=True, nullable=False)
    value_json = Column(Text, nullable=False)
    source = Column(String(64), default="AGENT")
    importance = Column(String(64), default="HIGH", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    confidence = Column(Float, default=1.0)
    status = Column(String(64), default="ACTIVE", index=True)  # ACTIVE, SUPERSEDED, ARCHIVED
    supersedes_id = Column(String(64), nullable=True)
    superseded_by = Column(String(64), nullable=True)
    tags_json = Column(Text, default="[]")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat(), index=True)
    updated_at = Column(String(64), default=lambda: datetime.now().isoformat())

    __table_args__ = (
        Index("idx_proj_mem_type", "project_id", "memory_type"),
        Index("idx_proj_mem_status", "project_id", "status"),
        Index("idx_proj_mem_key", "project_id", "key"),
    )


class CodebaseFileIndexModel(Base):
    __tablename__ = "codebase_file_indexes"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    file_path = Column(String(512), index=True, nullable=False)
    file_hash = Column(String(64), nullable=False)
    language = Column(String(64), default="text")
    size_bytes = Column(Integer, default=0)
    symbols_json = Column(Text, default="[]")
    imports_json = Column(Text, default="[]")
    exports_json = Column(Text, default="[]")
    last_indexed = Column(String(64), default=lambda: datetime.now().isoformat())

    __table_args__ = (
        Index("idx_code_proj_path", "project_id", "file_path"),
        Index("idx_code_proj_hash", "project_id", "file_hash"),
    )


class CodeDependencyModel(Base):
    __tablename__ = "code_dependencies"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    source_file = Column(String(512), index=True, nullable=False)
    target_file_or_symbol = Column(String(512), index=True, nullable=False)
    relationship = Column(String(64), default="IMPORTS", index=True)  # IMPORTS, CALLS, ROUTES_TO, USES, EXTENDS, DEPENDS_ON
    metadata_json = Column(Text, default="{}")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat())

    __table_args__ = (
        Index("idx_dep_proj_src", "project_id", "source_file"),
        Index("idx_dep_proj_rel", "project_id", "relationship"),
    )


class ProjectVersionSnapshotModel(Base):
    __tablename__ = "project_version_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    version_num = Column(Integer, default=1, index=True)
    version_tag = Column(String(64), default="v1")
    request = Column(Text, default="")
    files_snapshot_json = Column(Text, default="{}")
    changed_files_json = Column(Text, default="[]")
    memory_delta_json = Column(Text, default="{}")
    test_results_json = Column(Text, default="{}")
    created_at = Column(String(64), default=lambda: datetime.now().isoformat(), index=True)

    __table_args__ = (
        Index("idx_ver_proj_num", "project_id", "version_num"),
    )


