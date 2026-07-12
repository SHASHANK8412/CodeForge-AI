from fastapi import APIRouter, Query

from backend.memory.memory_manager import memory_manager

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/history")
def get_memory_history(session_id: str = Query(default="default")):
    return {
        "session_id": session_id,
        "history": memory_manager.get_history(session_id),
    }


@router.get("/project")
def get_project_memory(session_id: str = Query(default="default")):
    return {
        "session_id": session_id,
        "project": memory_manager.get_project(session_id),
    }


@router.delete("/clear")
def clear_memory(session_id: str = Query(default="default")):
    memory_manager.clear_session(session_id)
    return {
        "session_id": session_id,
        "success": True,
    }
