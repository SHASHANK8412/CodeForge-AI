"""
AIForge Day 96 & 97 Master Learning Engine
==========================================
Master orchestrator integrating:
1. Long-Term Project Memory Storage
2. Semantic Vector Similarity Search
3. Reusable Knowledge Base & Templates
4. AI Reflection Engine & Quality Reports
5. Continuous Improvement Engine & Lessons Learned
"""

import logging
from typing import Dict, Any, List, Optional

from backend.learning.project_memory import global_project_memory_store
from backend.learning.similarity import global_semantic_similarity_engine
from backend.learning.knowledge_base import global_knowledge_base
from backend.learning.reflection import global_ai_reflection_engine
from backend.learning.improvement_engine import global_improvement_engine
from backend.learning.feedback import global_feedback_engine

_logger = logging.getLogger("aiforge.learning.engine")


class Day96LearningEngine:
    """
    Day 96 & 97 Continuous Learning & Autonomous Self-Improvement Engine.
    """

    def store_completed_project(
        self,
        prompt: str,
        architecture: str = "FastAPI + React",
        agents_used: Optional[List[str]] = None,
        generated_files: Optional[List[str]] = None,
        bugs: Optional[List[str]] = None,
        fixes: Optional[List[str]] = None,
        tests: Optional[Dict[str, Any]] = None,
        review_score: float = 95.6,
        performance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stores finished project into long-term project memory database.
        """
        return global_project_memory_store.store_project(
            prompt=prompt,
            architecture=architecture,
            agents_used=agents_used,
            generated_files=generated_files,
            bugs=bugs,
            fixes=fixes,
            tests=tests,
            review_score=review_score,
            performance=performance
        )

    def retrieve_similar_projects(self, prompt: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Semantic vector search for similar previous projects.
        """
        return global_semantic_similarity_engine.find_similar_projects(prompt, top_k=top_k)

    def get_knowledge_catalog(self) -> Dict[str, Any]:
        """
        Returns catalog of reusable component templates & best practices.
        """
        return global_knowledge_base.get_all_knowledge()

    def generate_reflection_report(self, project_name: str, **kwargs) -> Dict[str, Any]:
        """
        Generates AI Reflection & Quality Score Report.
        """
        return global_ai_reflection_engine.generate_reflection(project_name, **kwargs)

    def get_lessons_learned(self) -> Dict[str, Any]:
        """
        Returns extracted lessons learned from historical project builds.
        """
        return global_improvement_engine.analyze_and_extract_lessons()


global_day96_learning_engine = Day96LearningEngine()
