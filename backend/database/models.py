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
