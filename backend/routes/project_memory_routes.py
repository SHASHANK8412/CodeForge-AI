"""
AIForge REST APIs — Persistent Project Memory & Codebase Intelligence
======================================================================
Provides endpoints for:
- Project Memory CRUD, search, and conflict superseding
- Incremental codebase indexing and symbol search
- Code dependency graph inspection
- Change impact analysis
- Project version lineage and reopening
"""

import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from backend.memory.project_memory_service import global_project_memory_service
from backend.memory.codebase_indexer import global_codebase_indexer
from backend.memory.dependency_graph import global_dependency_graph
from backend.memory.impact_analyzer import global_impact_analyzer, ImpactReport
from backend.quality.version_manager import global_version_manager
from backend.generation.manager import GenerationManager

router = APIRouter(prefix="/api/projects", tags=["Project Memory & Codebase Intelligence"])
_logger = logging.getLogger("aiforge.routes.project_memory")
_gen_manager = GenerationManager()


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class CreateMemoryPayload(BaseModel):
    memory_type: str = Field(default="ARCHITECTURE", description="REQUIREMENT, ARCHITECTURE, DECISION, CONVENTION, USER_PREFERENCE, DATABASE, API")
    key: str = Field(..., description="Unique memory key (e.g. database_choice, auth_method)")
    value: Any = Field(..., description="Memory value string or structured object")
    source: str = Field(default="USER", description="USER, ARCHITECT, PLANNER, DEBUGGER")
    importance: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    tags: List[str] = Field(default_factory=list)
    supersedes_key: Optional[str] = Field(default=None, description="Key of older memory being superseded")


class ImpactAnalysisPayload(BaseModel):
    targets: List[str] = Field(default_factory=list, description="Target files or symbols being modified")
    prompt: str = Field(default="", description="User prompt describing proposed change")


class ModifyProjectPayload(BaseModel):
    prompt: str = Field(..., description="Instruction to modify existing project (e.g. 'Add wishlist')")
    user_id: str = Field(default="default_user")


# ---------------------------------------------------------------------------
# Project Profile & Reopening Endpoints
# ---------------------------------------------------------------------------

@router.get("")
def list_projects() -> List[Dict[str, Any]]:
    """Lists all stored projects with metadata, version counts, test status, and memory summary."""
    projects_dict: Dict[str, Dict[str, Any]] = {}
    
    # 1. Inspect version history
    for proj_id, versions in global_version_manager._history.items():
        latest = versions[-1] if versions else None
        projects_dict[proj_id] = {
            "project_id": proj_id,
            "name": proj_id,
            "version": latest.version_id if latest else "v1",
            "version_count": len(versions),
            "files_count": len(latest.files_snapshot) if latest else 0,
            "test_status": latest.test_result.get("status", "PASS") if latest else "PASS",
            "quality_score": latest.quality_score if latest else 100.0,
            "last_updated": latest.created_at if latest else 0.0,
        }

    # 2. Add projects with tier memories
    all_tier_mems = global_project_memory_service._load_tier_memories()
    for proj_id, mems in all_tier_mems.items():
        if proj_id not in projects_dict:
            projects_dict[proj_id] = {
                "project_id": proj_id,
                "name": proj_id,
                "version": "v1",
                "version_count": 1,
                "files_count": 0,
                "test_status": "PASS",
                "quality_score": 100.0,
                "last_updated": 0.0,
            }
        projects_dict[proj_id]["active_memories_count"] = len([m for m in mems.values() if m.get("status") == "ACTIVE"])

    return list(projects_dict.values())


@router.get("/{project_id}")
def get_project_profile(project_id: str) -> Dict[str, Any]:
    """Retrieves detailed project profile, latest files snapshot, active memories, and version lineage."""
    latest_ver = global_version_manager.get_latest_version(project_id)
    versions = global_version_manager.get_history(project_id)
    active_mems = global_project_memory_service.get_active_memories(project_id)
    codebase_idx = global_codebase_indexer.get_project_index(project_id)
    dep_graph = global_dependency_graph.get_graph(project_id)

    files_snapshot = latest_ver.files_snapshot if latest_ver else {}

    return {
        "project_id": project_id,
        "name": project_id,
        "latest_version": latest_ver.version_id if latest_ver else "v1",
        "versions": [v.model_dump() for v in versions],
        "files_count": len(files_snapshot),
        "files_list": list(files_snapshot.keys()),
        "active_memories": active_mems,
        "codebase_summary": {
            "total_indexed_files": len(codebase_idx),
            "dependency_nodes": dep_graph.get("node_count", len(dep_graph.get("nodes", []))),
            "dependency_edges": dep_graph.get("edge_count", len(dep_graph.get("edges", []))),
        },
        "test_results": latest_ver.test_result if latest_ver else {},
        "quality_score": latest_ver.quality_score if latest_ver else 100.0,
    }


# ---------------------------------------------------------------------------
# Project Memory Endpoints
# ---------------------------------------------------------------------------

@router.get("/{project_id}/memory")
def get_project_memories(
    project_id: str,
    memory_type: Optional[str] = Query(None, description="Filter by memory_type"),
    include_superseded: bool = Query(False, description="Include superseded memories"),
    search: Optional[str] = Query(None, description="Search query")
) -> List[Dict[str, Any]]:
    """Retrieves memories for a project with optional search and superseded history."""
    if search:
        return global_project_memory_service.search_project_memories(project_id, search)
    if include_superseded:
        mems = global_project_memory_service.get_all_memories(project_id, include_superseded=True)
        if memory_type:
            mems = [m for m in mems if m.get("memory_type") == memory_type.upper()]
        return mems
    return global_project_memory_service.get_active_memories(project_id, memory_type=memory_type)


@router.post("/{project_id}/memory")
def save_project_memory(project_id: str, payload: CreateMemoryPayload) -> Dict[str, Any]:
    """Stores a new project memory item with automatic conflict superseding."""
    created = global_project_memory_service.save_project_memory(
        project_id=project_id,
        memory_type=payload.memory_type,
        key=payload.key,
        value=payload.value,
        source=payload.source,
        importance=payload.importance,
        tags=payload.tags,
        supersedes_key=payload.supersedes_key,
    )
    return {"status": "SUCCESS", "memory": created}


@router.delete("/{project_id}/memory/{memory_id}")
def delete_project_memory(project_id: str, memory_id: str) -> Dict[str, Any]:
    """Deletes a memory item by ID."""
    success = global_project_memory_service.delete_project_memory(project_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "SUCCESS", "deleted_id": memory_id}


# ---------------------------------------------------------------------------
# Codebase Intelligence & Index Endpoints
# ---------------------------------------------------------------------------

@router.get("/{project_id}/codebase/index")
def get_codebase_index(project_id: str) -> Dict[str, Any]:
    """Retrieves the full codebase index metadata for a project."""
    return global_codebase_indexer.get_project_index(project_id)


@router.get("/{project_id}/codebase/search")
def search_codebase(
    project_id: str,
    query: str = Query(..., description="Search query by path, symbol, route, or component"),
    top_k: int = Query(10, description="Max results")
) -> List[Dict[str, Any]]:
    """Searches the indexed codebase symbols, routes, and components."""
    return global_codebase_indexer.search_codebase(project_id, query, top_k=top_k)


@router.get("/{project_id}/codebase/dependencies")
def get_dependency_graph(project_id: str) -> Dict[str, Any]:
    """Retrieves the project code dependency graph (nodes & directed edges)."""
    return global_dependency_graph.get_graph(project_id)


@router.post("/{project_id}/codebase/impact")
def analyze_change_impact(project_id: str, payload: ImpactAnalysisPayload) -> ImpactReport:
    """Computes the change impact radius for target files/symbols or a feature prompt."""
    return global_impact_analyzer.analyze_change_impact(
        project_id=project_id,
        targets=payload.targets,
        prompt=payload.prompt
    )


@router.post("/{project_id}/codebase/reindex")
def reindex_codebase(project_id: str, force: bool = Query(False)) -> Dict[str, Any]:
    """Triggers an incremental or forced re-indexing of project files."""
    latest_ver = global_version_manager.get_latest_version(project_id)
    if not latest_ver or not latest_ver.files_snapshot:
        return {"status": "SKIPPED", "message": "No files found for project"}

    res = global_codebase_indexer.index_project_files(project_id, latest_ver.files_snapshot, force_reindex=force)
    proj_idx = global_codebase_indexer.get_project_index(project_id)
    global_dependency_graph.build_graph_from_index(project_id, proj_idx)
    return {"status": "SUCCESS", "metrics": res}


# ---------------------------------------------------------------------------
# Project Modification Execution Endpoint
# ---------------------------------------------------------------------------

@router.post("/{project_id}/modify")
async def modify_existing_project(project_id: str, payload: ModifyProjectPayload) -> Dict[str, Any]:
    """Launches an autonomous generation pipeline modifying the existing project."""
    gen_id = _gen_manager.create(
        project_id=project_id,
        user_id=payload.user_id,
        prompt=payload.prompt
    )
    # Launch async background pipeline
    import asyncio
    asyncio.create_task(_gen_manager.run(gen_id))

    return {
        "status": "QUEUED",
        "project_id": project_id,
        "generation_id": gen_id,
        "prompt": payload.prompt,
        "message": f"Modifying existing project '{project_id}'"
    }
