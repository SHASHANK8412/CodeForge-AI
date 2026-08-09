"""
AIForge Knowledge Package
=========================
Knowledge Extractor, Knowledge Graph Builder, Project Memory, Recommender Engine, Continuous Learning Engine, and Semantic Knowledge Retriever.
"""

from backend.knowledge.extractor import KnowledgeExtractor, global_knowledge_extractor
from backend.knowledge.graph_builder import KnowledgeGraphBuilder, global_knowledge_graph_builder
from backend.knowledge.project_memory import ProjectMemoryStore, global_project_memory_store
from backend.knowledge.recommender import RecommendationEngine, global_recommendation_engine
from backend.knowledge.learning_engine import LearningEngine, global_learning_engine
from backend.knowledge.retriever import KnowledgeRetriever, global_knowledge_retriever

__all__ = [
    "KnowledgeExtractor", "global_knowledge_extractor",
    "KnowledgeGraphBuilder", "global_knowledge_graph_builder",
    "ProjectMemoryStore", "global_project_memory_store",
    "RecommendationEngine", "global_recommendation_engine",
    "LearningEngine", "global_learning_engine",
    "KnowledgeRetriever", "global_knowledge_retriever"
]
