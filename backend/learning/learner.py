"""
AIForge Day 93 Master Learner & Continuous Improvement Orchestrator
===================================================================
1. Evaluates projects with weighted Learning Score (30% Arch, 20% Code, 20% Tests, 15% Perf, 10% Doc, 5% Sec)
2. Calculates Performance Metrics (Gen Time, Tokens, Retries, Errors, Success Rate, Test Score, Review Score)
3. Retrieves Similar Projects & reusable components/APIs
4. Updates Project Memory, Mistakes DB, and Best Practices DB
5. Generates Improvement Suggestions & Prompt Refinements
"""

import logging
from typing import Dict, Any, List, Optional

from backend.learning.evaluator import global_learning_evaluator
from backend.learning.similarity import global_similar_retriever
from backend.learning.metrics import global_analytics_collector
from backend.learning.feedback import global_feedback_engine
from backend.learning.trainer import global_knowledge_trainer
from backend.agents.learning_agent import global_learning_agent

_logger = logging.getLogger("aiforge.learning.learner")


class MasterLearningOrchestrator:
    """
    Day 93 Master Learner for Continuous Software Engineering Improvement.
    """

    def evaluate_project(
        self,
        project_name: str,
        architecture_score: float = 95.0,
        code_quality_score: float = 92.0,
        tests_score: float = 94.0,
        performance_score: float = 96.0,
        documentation_score: float = 90.0,
        security_score: float = 98.0
    ) -> Dict[str, Any]:
        """
        Calculates weighted Learning Score (30% Arch, 20% Code, 20% Tests, 15% Perf, 10% Doc, 5% Sec).
        """
        return global_learning_evaluator.evaluate_learning_score(
            project_name=project_name,
            architecture_score=architecture_score,
            code_quality_score=code_quality_score,
            tests_score=tests_score,
            performance_score=performance_score,
            documentation_score=documentation_score,
            security_score=security_score
        )

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculates telemetry metrics for performance dashboard.
        """
        return global_analytics_collector.calculate_performance_metrics()

    def retrieve_similar_projects(self, prompt: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves similar projects for prompt reuse.
        """
        return global_similar_retriever.find_similar_projects(prompt, top_k=top_k)

    def update_knowledge(
        self,
        project_name: str,
        framework: str = "React",
        backend: str = "FastAPI",
        bugs: int = 1,
        tests_passed: int = 94,
        rating: int = 5,
        learning_score: int = 94
    ) -> Dict[str, Any]:
        """
        Updates persistent knowledge bases (project_memory.json, best_practices.json).
        """
        return global_knowledge_trainer.train_on_project_outcome(
            project_name=project_name,
            framework=framework,
            backend=backend,
            bugs=bugs,
            tests_passed=tests_passed,
            rating=rating,
            learning_score=learning_score
        )

    def record_mistake(self, problem: str, solution: str, category: str = "general") -> Dict[str, Any]:
        """
        Records recurring mistake into mistakes.json.
        """
        return global_feedback_engine.record_mistake(problem=problem, solution=solution, category=category)

    def get_best_practices(self) -> List[Dict[str, Any]]:
        """
        Returns list of stored best practices.
        """
        import json
        from pathlib import Path
        bp_file = Path(__file__).resolve().parent.parent / "knowledge" / "best_practices.json"
        if bp_file.exists():
            try:
                with open(bp_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def generate_recommendations(self, current_coverage_pct: float = 65.0) -> Dict[str, Any]:
        """
        Generates improvement suggestions and expected coverage metrics.
        """
        return global_feedback_engine.generate_improvement_suggestions(current_coverage_pct=current_coverage_pct)

    def refine_prompt(self, base_prompt: str) -> str:
        """
        Refines short prompt into production-ready enhanced prompt.
        """
        return global_feedback_engine.refine_prompt(base_prompt)

    def query_prior_knowledge(self, prompt: str) -> Dict[str, Any]:
        """
        Pre-generation query: checks similar projects, best practices, and known mistakes.
        """
        similar = self.retrieve_similar_projects(prompt)
        enhanced_prompt = self.refine_prompt(prompt)
        best_practices = self.get_best_practices()
        mistakes = global_feedback_engine.get_all_mistakes()

        return {
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "similar_projects": similar,
            "similar_project_found": len(similar) > 0,
            "best_practices_count": len(best_practices),
            "known_mistakes_count": len(mistakes),
            "suggested_architecture": similar[0]["architecture"] if similar else "FastAPI + React",
            "suggested_components": similar[0]["reusable_components"] if similar else ["Navbar", "Sidebar", "MainLayout"]
        }


global_master_learner = MasterLearningOrchestrator()
ProjectLearnerEngine = MasterLearningOrchestrator
MasterProjectLearner = MasterLearningOrchestrator
