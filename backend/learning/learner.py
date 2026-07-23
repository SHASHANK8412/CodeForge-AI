"""
AIForge Master Project Intelligence Learner
===========================================
Master Project Intelligence orchestrator for Day 76:
- Analyzes completed projects (tech stack, framework, auth, architecture, components, patterns)
- Scores project quality (Architecture, Code Quality, Security, Testing, Performance)
- Persists project intelligence in ProjectMemoryDB & ChromaDB embeddings
- Queries similarity search to enable knowledge reuse for new project requests
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.learning.project_memory import ProjectMemoryDB
from backend.learning.embeddings import EmbeddingsGenerator
from backend.learning.similarity import SimilaritySearchEngine
from backend.learning.scorer import QualityScorer

_logger = logging.getLogger("aiforge.learning")


class MasterProjectLearner:
    """
    Master Learner orchestrating Project Memory DB, similarity search, and quality scoring.
    """

    def __init__(self) -> None:
        self.db = ProjectMemoryDB()
        self.embeddings = EmbeddingsGenerator()
        self.similarity_engine = SimilaritySearchEngine(db=self.db)
        self.scorer = QualityScorer()

    def query_prior_knowledge(self, user_prompt: str) -> Dict[str, Any]:
        """
        Asks: "Have I solved something similar before?"
        If YES, returns reusable patterns and architecture to prevent building from scratch.
        """
        _logger.info(f"MasterProjectLearner: Asking 'Have I solved something similar before?' for prompt: '{user_prompt}'")
        return self.similarity_engine.get_reusable_patterns(user_prompt)

    def learn_from_project(
        self,
        project_name: str,
        tech_stack: List[str],
        architecture: str = "FastAPI + React",
        authentication: str = "JWT",
        database_type: str = "SQLite",
        frontend_framework: str = "React + Tailwind",
        design_patterns: Optional[List[str]] = None,
        syntax_errors: int = 0,
        test_pass_rate: float = 100.0,
        bugs_fixed_count: int = 0,
        execution_time_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Analyzes project, scores quality, and stores intelligence in ProjectMemoryDB.
        """
        _logger.info(f"MasterProjectLearner: Learning from project '{project_name}'...")
        design_patterns = design_patterns or ["Repository", "MVC", "JWT Middleware"]

        # Calculate quality score
        score_info = self.scorer.score_project(
            syntax_errors=syntax_errors,
            test_pass_rate=test_pass_rate,
            security_passed=True,
            execution_time_seconds=execution_time_seconds
        )
        overall_score = score_info["overall_score"]

        # Persist project intelligence
        saved_record = self.db.save_project(
            project_name=project_name,
            tech_stack=tech_stack,
            architecture=architecture,
            authentication=authentication,
            database_type=database_type,
            frontend_framework=frontend_framework,
            design_patterns=design_patterns,
            quality_score=overall_score,
            bugs_fixed_count=bugs_fixed_count,
            raw_summary=score_info
        )

        return {
            "status": "success",
            "project_name": project_name,
            "overall_score": overall_score,
            "score_breakdown": score_info,
            "saved_record": saved_record
        }


global_project_learner = MasterProjectLearner()
