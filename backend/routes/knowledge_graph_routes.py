"""
AIForge REST API — Knowledge Graph & Graph RAG Intelligence Layer
=================================================================
Endpoints:
- GET  /api/knowledge/graph
- GET  /api/knowledge/entities
- GET  /api/knowledge/entities/{entity_id}
- GET  /api/knowledge/entities/{entity_id}/neighbors
- POST /api/knowledge/query
- POST /api/knowledge/path
- POST /api/knowledge/traverse
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.knowledge_graph.graph_store import global_graph_store
from backend.knowledge_graph.graph_rag import global_graph_rag

router = APIRouter(prefix="/api/knowledge", tags=["AIForge Knowledge Graph & Graph RAG"])


class GraphRAGQueryPayload(BaseModel):
    query: str
    project_id: Optional[str] = "aiforge-fooddelivery-ai"
    max_hops: Optional[int] = 2


class FindPathPayload(BaseModel):
    start_entity_id: str
    end_entity_id: str
    max_depth: Optional[int] = 3


class TraversePayload(BaseModel):
    root_entity_id: str
    depth: Optional[int] = 2


@router.get("/graph")
def get_full_graph(project_id: Optional[str] = Query("aiforge-fooddelivery-ai")):
    graph = global_graph_store.get_full_graph(project_id=project_id)
    return {
        "success": True,
        "graph": graph
    }


@router.get("/entities")
def list_entities():
    nodes = list(global_graph_store._nodes.values())
    return {
        "success": True,
        "count": len(nodes),
        "entities": [n.model_dump() for n in nodes]
    }


@router.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    node = global_graph_store.get_node(entity_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return {
        "success": True,
        "entity": node.model_dump()
    }


@router.get("/entities/{entity_id}/neighbors")
def get_entity_neighbors(entity_id: str):
    neighbors = global_graph_store.get_neighbors(entity_id)
    if not neighbors.get("node"):
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return {
        "success": True,
        "node": neighbors["node"].model_dump(),
        "outgoing": [{"edge": o["edge"].model_dump(), "target_node": o["target_node"].model_dump() if o["target_node"] else None} for o in neighbors["outgoing"]],
        "incoming": [{"edge": i["edge"].model_dump(), "source_node": i["source_node"].model_dump() if i["source_node"] else None} for i in neighbors["incoming"]]
    }


@router.post("/query", status_code=status.HTTP_200_OK)
def query_graph_rag(payload: GraphRAGQueryPayload):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    res = global_graph_rag.query(
        query_text=payload.query,
        project_id=payload.project_id or "aiforge-fooddelivery-ai",
        max_hops=payload.max_hops or 2
    )
    return {
        "success": True,
        "result": res.model_dump()
    }


@router.post("/path")
def find_graph_path(payload: FindPathPayload):
    paths = global_graph_store.find_path(
        start_id=payload.start_entity_id,
        end_id=payload.end_entity_id,
        max_depth=payload.max_depth or 3
    )
    return {
        "success": True,
        "paths": paths
    }


@router.post("/traverse")
def traverse_dependency_tree(payload: TraversePayload):
    tree = global_graph_store.traverse_dependency_tree(
        root_id=payload.root_entity_id,
        depth=payload.depth or 2
    )
    return {
        "success": True,
        "tree": tree
    }
