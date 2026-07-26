"""
AIForge V2 – Persistent Memory System Database Models
=====================================================
SQLAlchemy ORM models for Projects, Tasks, Conversations, and Agent Telemetry Execution Logs.
"""

import time
import uuid
from sqlalchemy import Column, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from v2.database.db import Base


class ProjectModelV2(Base):
    __tablename__ = "v2_projects"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="active")
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time, onupdate=time.time)

    tasks = relationship("TaskModelV2", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("ConversationModelV2", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("AgentLogModelV2", back_populates="project", cascade="all, delete-orphan")


class TaskModelV2(Base):
    __tablename__ = "v2_tasks"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), ForeignKey("v2_projects.id", ondelete="CASCADE"), nullable=False)
    agent = Column(String(64), nullable=False)
    prompt = Column(Text, nullable=False)
    result = Column(Text, nullable=True)
    status = Column(String(32), default="completed")
    execution_time = Column(Float, default=0.0)
    timestamp = Column(Float, default=time.time)

    project = relationship("ProjectModelV2", back_populates="tasks")


class ConversationModelV2(Base):
    __tablename__ = "v2_conversations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), ForeignKey("v2_projects.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), nullable=False)  # user, assistant, agent
    message = Column(Text, nullable=False)
    created_at = Column(Float, default=time.time)

    project = relationship("ProjectModelV2", back_populates="conversations")


class AgentLogModelV2(Base):
    __tablename__ = "v2_agent_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), ForeignKey("v2_projects.id", ondelete="CASCADE"), nullable=True)
    agent = Column(String(64), nullable=False)
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    duration = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    timestamp = Column(Float, default=time.time)

    project = relationship("ProjectModelV2", back_populates="logs")
