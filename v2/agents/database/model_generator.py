"""
AIForge V2 – SQLAlchemy Model Generator
=======================================
Generates production-ready SQLAlchemy ORM models (`User`, `Project`, `Task`, `AgentLog`).
"""


class SQLAlchemyModelGenerator:

    def generate_models_code(self, project_name: str) -> str:
        return """import time
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="user")

    projects = relationship("ProjectModel", back_populates="owner", cascade="all, delete-orphan")

class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(256), nullable=False)
    complexity_tier = Column(String(32), default="medium")
    status = Column(String(32), default="active")

    owner = relationship("UserModel", back_populates="projects")
    tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assigned_agent = Column(String(64), nullable=False)
    title = Column(String(256), nullable=False)
    status = Column(String(32), default="pending")

    project = relationship("ProjectModel", back_populates="tasks")
"""


global_model_generator = SQLAlchemyModelGenerator()
