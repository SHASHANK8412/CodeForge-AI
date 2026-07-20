import time
import logging
from typing import Dict, Any, List
from backend.learning.learning_memory import LearningMemory
from backend.learning.experience_db import ExperienceDatabase
from backend.learning.pattern_recognizer import PatternRecognizer
from backend.learning.prompt_optimizer import PromptOptimizer
from backend.learning.best_practices import BestPracticesGenerator
from backend.learning.performance_tracker import PerformanceTracker
from backend.learning.architecture_evolver import ArchitectureEvolver
from backend.learning.confidence_scorer import ConfidenceScorer
from backend.learning.reflection_engine import ReflectionEngine

_logger = logging.getLogger("aiforge.learning")

class LearningPipeline:
    """
    Orchestrates the entire continuous learning lifecycle:
    Project -> Scorer -> Tracker -> Pattern Recognizer -> prompt optimizer -> Memory Save.
    """

    def __init__(self) -> None:
        self.memory = LearningMemory()
        self.experience_db = ExperienceDatabase(memory=self.memory)
        self.pattern_recognizer = PatternRecognizer(memory=self.memory)
        self.prompt_optimizer = PromptOptimizer()
        self.best_practices_gen = BestPracticesGenerator()
        self.performance_tracker = PerformanceTracker()
        self.architecture_evolver = ArchitectureEvolver(memory=self.memory)
        self.confidence_scorer = ConfidenceScorer()
        self.reflection_engine = ReflectionEngine()

    async def execute_post_project_learning(
        self,
        project_name: str,
        technologies: List[str],
        execution_metrics: Dict[str, Any],
        reviewer_feedback: str = "",
        syntax_errors: int = 0
    ) -> Dict[str, Any]:
        """
        Coordinates SRE analytics profiling, prompt refining, and commits summary json to memory.
        """
        _logger.info(f"Executing SRE Continuous Learning Pipeline for '{project_name}'...")

        # 1. Determine errors / mistakes
        mistakes: List[str] = []
        if syntax_errors > 0:
            mistakes.append("Syntax compilation issues")
        if "weak" in reviewer_feedback.lower() or "error" in reviewer_feedback.lower():
            mistakes.append("Reviewer architecture correction")

        # 2. Calculate file confidence
        confidence = self.confidence_scorer.calculate_confidence(
            file_path="main.py",
            review_passed=len(mistakes) == 0,
            tests_passed=syntax_errors == 0,
            deployment_passed=True,
            syntax_errors_count=syntax_errors
        )

        # 3. Track Performance metrics
        recommendations = self.performance_tracker.track_performance(execution_metrics)

        # 4. Prompt Optimization (if feedback is provided)
        if reviewer_feedback:
            # We refine the backend prompt dynamically based on criticisms
            self.prompt_optimizer.optimize_prompt("backend", reviewer_feedback)

        # 5. Extract best practices
        summary = {
            "project": project_name,
            "timestamp": time.time(),
            "technologies": technologies,
            "mistakes": mistakes,
            "fixes": ["Dynamic code revision loops" if mistakes else "None"],
            "best_practices": {
                "folder_structure": ["src/components/", "backend/routes/"],
                "api_design": ["Standardized REST endpoints", "GZip compressed"],
                "security_practices": ["JWT Validation filters"]
            },
            "performance": execution_metrics,
            "deployment_notes": "Compiled package checks passed.",
            "final_score": int(confidence)
        }
        
        self.best_practices_gen.update_best_practices(summary)

        # 6. Save summary to Learning Memory
        self.memory.save_project_summary(project_name, summary)

        # 7. Run SRE Pattern Analysis & Evolver updates
        self.pattern_recognizer.analyze_patterns()
        self.architecture_evolver.evolve_architecture()

        # 8. Retrospective reflection
        reflection_md = self.reflection_engine.generate_reflection(
            project_name=project_name,
            techs=technologies,
            mistakes=mistakes,
            success=syntax_errors == 0
        )

        return {
            "success": True,
            "confidence_score": confidence,
            "performance_recommendations": recommendations,
            "reflection": reflection_md
        }
