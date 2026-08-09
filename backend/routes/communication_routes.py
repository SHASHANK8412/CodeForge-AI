"""
FastAPI Routes for Day 30 Multi-Agent Collaboration & Communication Protocol
==============================================================================
Exposes REST APIs for inter-agent message exchanges, inbox management, event timeline, shared project context, dependency resolution, and collaboration dashboard.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.communication.protocol import AgentMessage, MessageType, MessagePriority
from backend.communication.message_bus import global_message_bus
from backend.communication.shared_context import global_shared_context
from backend.communication.events import global_event_dispatcher
from backend.communication.dependency_manager import global_dependency_manager
from backend.communication.conflict_resolution import global_conflict_resolver
from backend.communication.communication_logger import global_communication_logger

router = APIRouter(tags=["Agent Communication & Collaboration"])


class SendMessageInput(BaseModel):
    sender: str
    receiver: str
    type: Optional[str] = MessageType.TASK
    priority: Optional[str] = MessagePriority.MEDIUM
    payload: Dict[str, Any]


class UpdateContextInput(BaseModel):
    project_name: Optional[str] = None
    tech_stack: Optional[Dict[str, Any]] = None
    completed_tasks: Optional[List[str]] = None
    active_tasks: Optional[List[str]] = None
    updates: Optional[Dict[str, Any]] = None


class ResolveConflictInput(BaseModel):
    topic: str
    agent_a: str
    proposal_a: str
    agent_b: str
    proposal_b: str


@router.get("/messages")
@router.get("/api/v1/messages")
async def list_all_messages(agent: Optional[str] = Query(None, description="Filter by sender or receiver agent name")) -> Dict[str, Any]:
    """Retrieves all inter-agent messages on the Communication Bus."""
    messages = global_message_bus.get_all_messages(agent=agent)
    return {"status": "success", "total_messages": len(messages), "messages": messages}


@router.get("/messages/{agent}")
@router.get("/api/v1/messages/{agent}")
async def get_agent_inbox(agent: str, unread_only: bool = False) -> Dict[str, Any]:
    """Retrieves inbox messages queue for a specific agent."""
    inbox = global_message_bus.get_agent_inbox(agent, unread_only=unread_only)
    return {"status": "success", "agent": agent, "inbox_count": len(inbox), "inbox": inbox}


@router.post("/messages/send")
@router.post("/api/v1/messages/send")
async def send_agent_message(req: SendMessageInput) -> Dict[str, Any]:
    """Sends a structured AgentMessage across the central communication bus."""
    try:
        msg = AgentMessage(
            sender=req.sender,
            receiver=req.receiver,
            type=req.type or MessageType.TASK,
            priority=req.priority or MessagePriority.MEDIUM,
            payload=req.payload
        )
        delivered = global_message_bus.send_message(msg)
        return {"status": "success", "message_delivered": delivered}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events")
@router.get("/api/v1/events")
async def get_event_timeline(limit: int = 50) -> Dict[str, Any]:
    """Retrieves timeline of broadcast system events."""
    timeline = global_event_dispatcher.get_event_timeline(limit=limit)
    return {"status": "success", "total_events": len(timeline), "events": timeline}


@router.get("/context")
@router.get("/api/v1/context")
async def get_shared_project_context() -> Dict[str, Any]:
    """Retrieves the shared project context object accessible by all active agents."""
    ctx = global_shared_context.get_context()
    return {"status": "success", "context": ctx}


@router.post("/context/update")
@router.post("/api/v1/context/update")
async def update_shared_project_context(req: UpdateContextInput) -> Dict[str, Any]:
    """Updates shared project state, tech stack, or active tasks."""
    upd = req.updates or {}
    if req.project_name:
        upd["project_name"] = req.project_name
    if req.tech_stack:
        upd["tech_stack"] = req.tech_stack
    if req.completed_tasks is not None:
        upd["completed_tasks"] = req.completed_tasks
    if req.active_tasks is not None:
        upd["active_tasks"] = req.active_tasks

    updated_ctx = global_shared_context.update_state(upd)
    return {"status": "success", "updated_context": updated_ctx}


@router.get("/dependencies")
async def get_agent_dependencies() -> Dict[str, Any]:
    """Retrieves inter-agent task execution dependency graph."""
    deps = global_dependency_manager.get_all_dependencies_list()
    return {"status": "success", "dependencies": deps}


@router.post("/conflicts/resolve")
async def resolve_inter_agent_conflict(req: ResolveConflictInput) -> Dict[str, Any]:
    """Resolves conflicting agent outputs using priority hierarchy (PM > Reviewer > Testing > Architect > Dev)."""
    res = global_conflict_resolver.resolve_conflict(
        topic=req.topic,
        agent_a=req.agent_a,
        proposal_a=req.proposal_a,
        agent_b=req.agent_b,
        proposal_b=req.proposal_b
    )
    return {"status": "success", "conflict_resolution": res}


@router.get("/communication/dashboard")
@router.get("/api/v1/communication/dashboard")
async def get_communication_dashboard() -> Dict[str, Any]:
    """Retrieves Enhanced Collaboration Dashboard metrics: Live Feed, Agent Inbox Counts, Event Timeline, Dependency Graph, Shared Context Viewer."""
    all_msgs = global_message_bus.get_all_messages()
    events = global_event_dispatcher.get_event_timeline(limit=20)
    ctx = global_shared_context.get_context()
    deps = global_dependency_manager.get_all_dependencies_list()
    logs = global_communication_logger.get_logs(limit=20)
    conflicts = global_conflict_resolver.get_conflict_history()

    # Active agent inboxes summary
    agents = ["Planner Agent", "Architect Agent", "Frontend Agent", "Backend Agent", "Database Agent", "Testing Agent", "Reviewer Agent", "DevOps Agent"]
    inbox_counts = {
        agent: len(global_message_bus.get_agent_inbox(agent, unread_only=True))
        for agent in agents
    }

    return {
        "status": "success",
        "collaboration_dashboard": {
            "total_messages": len(all_msgs),
            "live_communication_feed": logs,
            "agent_inbox_counts": inbox_counts,
            "event_timeline": events,
            "dependency_graph": deps,
            "shared_context_viewer": ctx,
            "conflicts_resolved": conflicts
        }
    }
