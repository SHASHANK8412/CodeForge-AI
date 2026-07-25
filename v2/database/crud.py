"""
AIForge V2 – Database CRUD Operations
====================================
Reusable CRUD helpers for Projects, Tasks, Conversations, and Agent Telemetry.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from v2.database.models_memory import ProjectModelV2, TaskModelV2, ConversationModelV2, AgentLogModelV2
from v2.database.schemas_memory import ProjectCreateSchema, TaskCreateSchema, ConversationCreateSchema, AgentLogCreateSchema


# --- Projects CRUD ---

def create_project(db: Session, schema: ProjectCreateSchema) -> ProjectModelV2:
    project = ProjectModelV2(
        title=schema.title,
        description=schema.description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: str) -> Optional[ProjectModelV2]:
    return db.query(ProjectModelV2).filter(ProjectModelV2.id == project_id).first()


def list_projects(db: Session, skip: int = 0, limit: int = 100) -> List[ProjectModelV2]:
    return db.query(ProjectModelV2).offset(skip).limit(limit).all()


def update_project(db: Session, project_id: str, title: Optional[str] = None, status: Optional[str] = None) -> Optional[ProjectModelV2]:
    project = get_project(db, project_id)
    if not project:
        return None
    if title:
        project.title = title
    if status:
        project.status = status
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: str) -> bool:
    project = get_project(db, project_id)
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


# --- Tasks CRUD ---

def create_task(db: Session, schema: TaskCreateSchema) -> TaskModelV2:
    task = TaskModelV2(
        project_id=schema.project_id,
        agent=schema.agent,
        prompt=schema.prompt,
        result=schema.result,
        execution_time=schema.execution_time
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks_by_project(db: Session, project_id: str) -> List[TaskModelV2]:
    return db.query(TaskModelV2).filter(TaskModelV2.project_id == project_id).all()


# --- Conversations CRUD ---

def create_conversation(db: Session, schema: ConversationCreateSchema) -> ConversationModelV2:
    convo = ConversationModelV2(
        project_id=schema.project_id,
        role=schema.role,
        message=schema.message
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def get_conversation_history(db: Session, project_id: str) -> List[ConversationModelV2]:
    return db.query(ConversationModelV2).filter(ConversationModelV2.project_id == project_id).order_by(ConversationModelV2.created_at.asc()).all()


# --- Agent Logs CRUD ---

def create_agent_log(db: Session, schema: AgentLogCreateSchema) -> AgentLogModelV2:
    log_entry = AgentLogModelV2(
        project_id=schema.project_id,
        agent=schema.agent,
        input=schema.input,
        output=schema.output,
        duration=schema.duration,
        success=schema.success
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def list_logs_by_project(db: Session, project_id: str) -> List[AgentLogModelV2]:
    return db.query(AgentLogModelV2).filter(AgentLogModelV2.project_id == project_id).order_by(AgentLogModelV2.timestamp.asc()).all()
