"""
FastAPI Routes for Day 74-75 Project Knowledge Graph
===================================================
Exposes REST endpoints for building knowledge graphs, querying dependencies,
rendering D3 schemas, and exporting Mermaid architecture diagrams.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.graph.builder import GraphBuilder
from backend.graph.query_engine import GraphQueryEngine
from backend.graph.visualizer import GraphVisualizer

router = APIRouter(prefix="/api/v1/graph", tags=["Project Knowledge Graph"])

global_builder = GraphBuilder()
global_query_engine = GraphQueryEngine()
global_visualizer = GraphVisualizer()


class GraphQueryRequest(BaseModel):
    query: str


@router.post("/build")
async def build_knowledge_graph() -> Dict[str, Any]:
    """Scans codebase and constructs NetworkX Project Knowledge Graph."""
    try:
        G, summary = global_builder.build_graph()
        return {"status": "success", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_knowledge_graph(req: GraphQueryRequest) -> Dict[str, Any]:
    """Queries project dependencies, impact, and database schema in natural language."""
    try:
        result = global_query_engine.query(req.query)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization")
async def get_graph_visualization() -> Dict[str, Any]:
    """Returns D3.js schema for knowledge graph visualization."""
    try:
        d3_schema = global_visualizer.get_d3_schema(max_nodes=100)
        return {"status": "success", "schema": d3_schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
