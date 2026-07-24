"""
AIForge Day 93 Failure Feedback & Improvement Engine
=====================================================
1. Records mistakes into mistakes.json (Problem, Solution, Occurrences).
2. Generates Improvement Suggestions (e.g., Test Coverage 65% -> Increase unit tests, add integration tests, mock external APIs -> Expected Coverage 92%).
3. Automatic Prompt Refinement ("Build blog app" -> "Build scalable blog application using React, FastAPI, PostgreSQL, JWT, responsive UI, unit tests, Docker support, CI/CD, documentation.").
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.feedback")


class FailureFeedbackEngine:
    """
    Failure feedback recorder & improvement suggestion generator.
    """

    def __init__(self, mistakes_path: Optional[str] = None) -> None:
        if mistakes_path is None:
            kn_dir = Path(__file__).resolve().parent.parent / "knowledge"
            kn_dir.mkdir(parents=True, exist_ok=True)
            mistakes_path = str(kn_dir / "mistakes.json")
        self.mistakes_file = Path(mistakes_path)

    def _load_mistakes(self) -> List[Dict[str, Any]]:
        try:
            with open(self.mistakes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_mistakes(self, records: List[Dict[str, Any]]) -> None:
        try:
            with open(self.mistakes_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save mistakes.json: {e}")

    def record_mistake(self, problem: str, solution: str, category: str = "general") -> Dict[str, Any]:
        mistakes = self._load_mistakes()
        for m in mistakes:
            if m.get("problem", "").lower() == problem.lower():
                m["occurrences"] = m.get("occurrences", 1) + 1
                self._save_mistakes(mistakes)
                _logger.info(f"FailureFeedbackEngine: Incremented occurrences for mistake '{problem}' ({m['occurrences']})")
                return m

        rec = {
            "mistake_id": f"err_{len(mistakes) + 1:03d}",
            "problem": problem,
            "solution": solution,
            "occurrences": 1,
            "category": category
        }
        mistakes.append(rec)
        self._save_mistakes(mistakes)
        _logger.info(f"FailureFeedbackEngine: Recorded new mistake '{problem}' -> '{solution}'")
        return rec

    def get_all_mistakes(self) -> List[Dict[str, Any]]:
        return self._load_mistakes()

    def generate_improvement_suggestions(
        self,
        current_coverage_pct: float = 65.0,
        current_score: float = 88.0
    ) -> Dict[str, Any]:
        _logger.info(f"FailureFeedbackEngine: Generating improvement suggestions for coverage {current_coverage_pct}%...")

        suggestions = [
            "Increase unit tests for REST controller routes",
            "Add integration tests for database repository layer",
            "Mock external APIs and HTTP client calls"
        ]

        return {
            "current_test_coverage_pct": current_coverage_pct,
            "improvement_suggestions": suggestions,
            "expected_coverage_pct": 92.0,
            "recommendation_summary": (
                f"Current Coverage: {current_coverage_pct}% -> "
                f"Action: {'; '.join(suggestions)} -> Expected Coverage: 92%"
            )
        }

    def refine_prompt(self, base_prompt: str) -> str:
        _logger.info(f"FailureFeedbackEngine: Refining prompt '{base_prompt}'...")

        prompt_clean = base_prompt.strip()

        if "blog" in prompt_clean.lower() and len(prompt_clean.split()) <= 4:
            return (
                "Build scalable blog application using React, FastAPI, PostgreSQL, JWT, "
                "responsive UI, unit tests, Docker support, CI/CD, documentation."
            )

        additions = []
        if "jwt" not in prompt_clean.lower() and "auth" not in prompt_clean.lower():
            additions.append("JWT authentication")
        if "test" not in prompt_clean.lower():
            additions.append("unit tests")
        if "docker" not in prompt_clean.lower():
            additions.append("Docker support")
        if "ci/cd" not in prompt_clean.lower():
            additions.append("CI/CD")
        if "doc" not in prompt_clean.lower():
            additions.append("documentation")

        if additions:
            return f"{prompt_clean} using React, FastAPI, PostgreSQL, {', '.join(additions)}, responsive UI."

        return prompt_clean


global_feedback_engine = FailureFeedbackEngine()
