"""
FastAPI Routes for Day 35 AI Memory, Knowledge Graph & Continuous Learning Engine
===================================================================================
Exposes REST APIs for knowledge extraction, semantic search, reusable component recommendations, knowledge graph querying, learning stats, and knowledge dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.knowledge.extractor import global_knowledge_extractor
from backend.knowledge.graph_builder import global_knowledge_graph_builder
from backend.knowledge.project_memory import global_project_memory_store
from backend.knowledge.recommender import global_recommendation_engine
from backend.knowledge.learning_engine import global_learning_engine
from backend.knowledge.retriever import global_knowledge_retriever

router = APIRouter(tags=["AI Memory & Knowledge Engine"])


class ExtractKnowledgeInput(BaseModel):
    name: Optional[str] = "Project"
    language: Optional[str] = "Python"
    framework: Optional[str] = "FastAPI"
    database: Optional[str] = "PostgreSQL"
    patterns: Optional[List[str]] = None


class SearchKnowledgeInput(BaseModel):
    query: str


@router.post("/knowledge/extract")
@router.post("/api/v1/knowledge/extract")
async def extract_project_knowledge(req: ExtractKnowledgeInput) -> Dict[str, Any]:
    """Extracts architectural decisions, API patterns, and schemas from project artifacts."""
    try:
        p_dict = req.dict()
        extracted = global_knowledge_extractor.extract_knowledge(p_dict)
        
        # Store in project memory
        global_project_memory_store.record_project_memory(
            project_name=req.name or "Project",
            language=req.language or "Python",
            framework=req.framework or "FastAPI",
            database=req.database or "PostgreSQL",
            patterns=req.patterns
        )

        return {"status": "success", "extraction_result": extracted}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge/search")
@router.get("/api/v1/knowledge/search")
async def search_knowledge(q: str = Query(..., description="Query terms (e.g. JWT authentication, React dashboard)")) -> Dict[str, Any]:
    """Performs semantic search across historical implementations and decisions."""
    try:
        res = global_knowledge_retriever.search_knowledge(q)
        return {"status": "success", "search_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge/recommend")
@router.get("/api/v1/knowledge/recommend")
async def recommend_assets(
    project_type: Optional[str] = Query("web_app", description="Target application type (e.g. food_delivery, ecommerce, CRM)"),
    description: Optional[str] = Query("", description="Optional prompt or requirement description")
) -> Dict[str, Any]:
    """Recommends proven reusable components, Dockerfiles, schemas, and CI/CD templates."""
    res = global_recommendation_engine.recommend_for_project(project_type or "web_app", description or "")
    return {"status": "success", "recommendations": res}


@router.get("/knowledge/graph")
@router.get("/api/v1/knowledge/graph")
async def get_knowledge_graph(node_id: Optional[str] = Query(None, description="Filter related nodes by node ID")) -> Dict[str, Any]:
    """Retrieves the project Knowledge Graph nodes, edges, and relationship links."""
    if node_id:
        related = global_knowledge_graph_builder.get_related_nodes(node_id)
        return {"status": "success", "node_id": node_id, "related_nodes": related}
    else:
        graph = global_knowledge_graph_builder.get_full_graph()
        return {"status": "success", "knowledge_graph": graph}


@router.get("/knowledge/stats")
@router.get("/api/v1/knowledge/stats")
async def get_learning_stats() -> Dict[str, Any]:
    """Retrieves continuous learning statistics, top patterns, and growth metrics."""
    stats = global_learning_engine.get_learning_stats()
    return {"status": "success", "learning_stats": stats}


@router.get("/knowledge/dashboard")
@router.get("/api/v1/knowledge/dashboard")
async def get_knowledge_dashboard() -> Dict[str, Any]:
    """Retrieves Knowledge Dashboard data: Projects Learned, Reusable Components, Knowledge Graph, Top Patterns, Recommendations, Learning Progress."""
    stats = global_learning_engine.get_learning_stats()
    graph = global_knowledge_graph_builder.get_full_graph()
    projects = global_project_memory_store.get_all_projects()
    recs = global_recommendation_engine.recommend_for_project("Food Delivery App")

    return {
        "status": "success",
        "knowledge_dashboard": {
            "projects_learned": len(projects),
            "reusable_components_count": stats["reusable_components_count"],
            "knowledge_growth_rate": stats["knowledge_growth_rate"],
            "failure_preventions": stats["failure_prevention_count"],
            "top_patterns": stats["top_patterns"],
            "sample_recommendations": recs["recommendations"],
            "knowledge_graph": graph,
            "learned_projects": projects
        }
    }
