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


class LegacyPromptOptimizerWrapper:
    def enhance_user_prompt(self, prompt: str) -> str:
        return f"{prompt} (Enhanced with production standards: React, FastAPI, PostgreSQL, JWT Auth, Docker, OpenAPI)"


class LegacyExperienceStoreWrapper:
    def get_all_experiences(self) -> List[Dict[str, Any]]:
        return global_project_memory_store.get_all_projects()


class LegacyArchitectureMemoryWrapper:
    def get_all_architectures(self) -> Dict[str, Any]:
        return {
            "FastAPI + React": "Microservices with JWT Auth & PostgreSQL",
            "MERN": "React + Express + Node + MongoDB",
            "Next.js": "Next.js 14 App Router + TailwindCSS"
        }


class LegacyBestPracticesWrapper:
    def get_all_best_practices(self) -> Dict[str, Any]:
        return global_knowledge_base.get_all_knowledge()


class Day96LearningEngine:
    """
    Day 96 & 97 Continuous Learning & Autonomous Self-Improvement Engine.
    """

    def __init__(self) -> None:
        self.prompt_optimizer = LegacyPromptOptimizerWrapper()
        self.experience_store = LegacyExperienceStoreWrapper()
        self.architecture_memory = LegacyArchitectureMemoryWrapper()
        self.best_practices = LegacyBestPracticesWrapper()

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
        return global_semantic_similarity_engine.find_similar_projects(prompt, top_k=top_k)

    def query_prior_experience(self, prompt: str) -> List[Dict[str, Any]]:
        return self.retrieve_similar_projects(prompt)

    def run_learning_cycle(self, **kwargs) -> Dict[str, Any]:
        return self.store_completed_project(
            prompt=kwargs.get("user_prompt", "Application"),
            architecture=kwargs.get("architecture", "FastAPI + React")
        )

    def get_telemetry(self) -> Dict[str, Any]:
        return self.get_lessons_learned()

    def get_knowledge_catalog(self) -> Dict[str, Any]:
        return global_knowledge_base.get_all_knowledge()

    def generate_reflection_report(self, project_name: str, **kwargs) -> Dict[str, Any]:
        return global_ai_reflection_engine.generate_reflection(project_name, **kwargs)

    def get_lessons_learned(self) -> Dict[str, Any]:
        return global_improvement_engine.analyze_and_extract_lessons()


global_day96_learning_engine = Day96LearningEngine()
global_learning_engine = global_day96_learning_engine
