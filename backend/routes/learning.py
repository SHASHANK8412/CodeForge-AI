"""
AIForge Day 96 & 97 Learning & Knowledge API Router
====================================================
Endpoints:
- GET /learning
- GET /knowledge
"""

from fastapi import APIRouter
from backend.learning.learning_engine import global_day96_learning_engine
from backend.learning.knowledge_base import global_knowledge_base

router = APIRouter(tags=["Learning"])


@router.get("/learning")
def get_learning_status():
    lessons = global_day96_learning_engine.get_lessons_learned()
    return {
        "status": "active",
        "lessons_learned_count": lessons["total_lessons_learned"],
        "lessons": lessons["lessons"]
    }


@router.get("/knowledge")
def get_knowledge_catalog():
    return global_knowledge_base.get_all_knowledge()
