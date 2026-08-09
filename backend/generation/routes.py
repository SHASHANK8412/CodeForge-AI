"""
backend/generation/routes.py
=============================
FastAPI REST + SSE endpoints for the real-time generation engine.

Endpoints
---------
POST  /api/generations              — create + start a new generation
GET   /api/generations/{id}         — current status + agent list
GET   /api/generations/{id}/events  — paginated event history
GET   /api/generations/{id}/stream  — Server-Sent Events stream
POST  /api/generations/{id}/cancel  — cancel running generation

All endpoints:
  * Require authenticated user (via get_current_user dependency)
  * Enforce generation ownership (403 if user doesn't own generation)
  * Never expose raw stack traces or internal paths
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.generation.store import global_generation_store as _store
from backend.generation.event_bus import global_event_bus as _bus
from backend.generation.manager import global_generation_manager as _manager

_logger = logging.getLogger("aiforge.generation.routes")

router = APIRouter(prefix="/api/generations", tags=["Generation Engine"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateGenerationRequest(BaseModel):
    project_id: str
    prompt: str


class GenerationStatusResponse(BaseModel):
    generation_id: str
    project_id: str
    status: str
    current_agent: Optional[str]
    progress: int
    agents: list
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_owned(gen_id: str, user_id: str) -> Dict[str, Any]:
    """Return the generation record or raise HTTP 403/404."""
    rec = _store.get(gen_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found."
        )
    if rec.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this generation."
        )
    return rec


def _safe_status_response(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Strip internal fields before returning to the client."""
    agents = rec.get("agents", [])
    # Only include user-visible agent names (core pipeline order)
    visible_agents = [
        a for a in agents
        if a.get("name") in {
            "planner", "architect", "frontend", "backend", "database",
            "assembly", "reviewer", "documentation", "build_validation",
            "dependency_manager", "security_scan", "performance",
            "execution_validation", "testing", "debug", "patch",
            "packaging", "deployment",
        }
    ]
    return {
        "generation_id": rec.get("generation_id"),
        "project_id": rec.get("project_id"),
        "status": rec.get("status"),
        "current_agent": rec.get("current_agent"),
        "progress": rec.get("progress", 0),
        "agents": [
            {
                "name": a.get("name"),
                "status": a.get("status"),
                "started_at": a.get("started_at"),
                "completed_at": a.get("completed_at"),
                "duration": a.get("duration"),
                "retry_count": a.get("retry_count", 0),
                "error": a.get("error"),
            }
            for a in visible_agents
        ],
        "started_at": rec.get("started_at"),
        "completed_at": rec.get("completed_at"),
        "error": rec.get("error"),
        "created_at": rec.get("created_at"),
    }


# ---------------------------------------------------------------------------
# POST /api/generations — create + start generation
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_generation(
    req: CreateGenerationRequest,
    user: dict = Depends(get_current_user),
):
    """
    Creates a generation record and immediately starts the LangGraph pipeline
    in the background. Returns generation_id and initial status 'queued'.
    The HTTP request returns before the pipeline finishes.
    """
    user_id: str = user.get("id", "default")
    _logger.info(
        "Creating generation: project=%s user=%s prompt=%.40s...",
        req.project_id, user_id, req.prompt,
    )

    gen_id = _manager.create(
        project_id=req.project_id,
        user_id=user_id,
        prompt=req.prompt,
    )

    # Start the pipeline asynchronously — this does NOT block
    await _manager.run(gen_id)

    return {
        "generation_id": gen_id,
        "status": "queued",
        "message": "Generation started. Connect to the stream endpoint for real-time updates.",
    }


# ---------------------------------------------------------------------------
# GET /api/generations/{generationId} — status + agents
# ---------------------------------------------------------------------------

@router.get("/{generation_id}")
async def get_generation_status(
    generation_id: str,
    user: dict = Depends(get_current_user),
):
    """Returns the current generation status and per-agent states."""
    user_id: str = user.get("id", "default")
    rec = _require_owned(generation_id, user_id)
    return _safe_status_response(rec)


# ---------------------------------------------------------------------------
# GET /api/generations/{generationId}/events — paginated event history
# ---------------------------------------------------------------------------

@router.get("/{generation_id}/events")
async def get_generation_events(
    generation_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """Returns paginated chronological events for a generation."""
    user_id: str = user.get("id", "default")
    _require_owned(generation_id, user_id)

    events = _store.get_events(generation_id, offset=offset, limit=limit)
    return {
        "generation_id": generation_id,
        "offset": offset,
        "limit": limit,
        "total": len(_store.get(generation_id, {}).get("events", [])),
        "events": events,
    }


# ---------------------------------------------------------------------------
# GET /api/generations/{generationId}/stream — SSE
# ---------------------------------------------------------------------------

@router.get("/{generation_id}/stream")
async def stream_generation_events(
    generation_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Server-Sent Events endpoint. Streams real-time agent lifecycle events.

    The client should first GET /api/generations/{id} to restore existing state,
    then open this stream to receive new events.

    Sends a heartbeat every ~25s to keep proxies from closing idle connections.
    Closes automatically when the generation completes, fails, or is cancelled.
    """
    user_id: str = user.get("id", "default")
    _require_owned(generation_id, user_id)

    async def event_stream():
        # Send current snapshot immediately so reconnecting clients are in sync
        rec = _store.get(generation_id, {})
        import json
        snapshot = _safe_status_response(rec)
        yield f"event: snapshot\ndata: {json.dumps(snapshot)}\n\n"

        # If the generation is already terminal, close immediately
        terminal = {"completed", "failed", "cancelled"}
        if rec.get("status") in terminal:
            yield "event: stream_done\ndata: {}\n\n"
            return

        # Subscribe to live events
        try:
            async for sse_line in _bus.subscribe(generation_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    _logger.info("SSE client disconnected from %s", generation_id)
                    return
                yield sse_line
        except Exception as exc:  # noqa: BLE001
            _logger.warning("SSE stream error for %s: %s", generation_id, exc)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# POST /api/generations/{generationId}/cancel
# ---------------------------------------------------------------------------

@router.post("/{generation_id}/cancel")
async def cancel_generation(
    generation_id: str,
    user: dict = Depends(get_current_user),
):
    """Requests cancellation of an active generation."""
    user_id: str = user.get("id", "default")
    _require_owned(generation_id, user_id)

    was_active = await _manager.cancel(generation_id)
    if was_active:
        return {
            "generation_id": generation_id,
            "status": "cancelled",
            "message": "Cancellation requested. The generation will stop shortly.",
        }
    return {
        "generation_id": generation_id,
        "status": _store.get(generation_id, {}).get("status", "unknown"),
        "message": "Generation is not currently active.",
    }


# ---------------------------------------------------------------------------
# GET /api/generations — list user's generations
# ---------------------------------------------------------------------------

@router.get("")
async def list_generations(
    user: dict = Depends(get_current_user),
):
    """Returns all generations belonging to the authenticated user."""
    user_id: str = user.get("id", "default")
    records = _store.get_by_user(user_id)
    return {
        "generations": [_safe_status_response(r) for r in records],
        "total": len(records),
    }
