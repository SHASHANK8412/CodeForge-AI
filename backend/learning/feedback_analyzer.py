"""
AIForge Learning - Feedback Analyzer
===================================
Analyzes generation history, error frequency, and reviewer feedback.
Classifies failures, computes success statistics, and generates actionable
remediation recommendations for the Learning Engine and Prompt Optimizer.
"""

import logging
from typing import Dict, Any, List
from backend.learning.experience_store import ExperienceStore

_logger = logging.getLogger("aiforge.learning")


class FeedbackAnalyzer:
    """
    Analyzes historical errors and user feedback to extract learning recommendations.
    """

    def __init__(self, store: ExperienceStore = None) -> None:
        if store is None:
            store = ExperienceStore()
        self.store = store

    def classify_error(self, error_msg: str) -> str:
        err_lower = error_msg.lower()
        if any(k in err_lower for k in ["auth", "jwt", "login", "unauthorized", "token"]):
            return "Missing Authentication"
        elif any(k in err_lower for k in ["validat", "sanitize", "input", "pydantic"]):
            return "Missing Input Validation"
        elif any(k in err_lower for k in ["import", "modulenotfound", "nameerror"]):
            return "Import / Dependency Issue"
        elif any(k in err_lower for k in ["syntax", "indentation", "unexpected token"]):
            return "Syntax Error"
        elif any(k in err_lower for k in ["cors", "access-control", "origin"]):
            return "CORS Misconfiguration"
        elif any(k in err_lower for k in ["db", "database", "sql", "mongo", "sqlite", "query"]):
            return "Database Query Error"
        else:
            return "General Engineering Flaw"

    def analyze_failures(self) -> Dict[str, Any]:
        return self.analyze_feedback()

    def analyze_feedback(self) -> Dict[str, Any]:
        experiences = self.store.get_all_experiences()
        error_counts: Dict[str, int] = {}
        total_errors_tracked = 0

        for exp in experiences:
            errors = exp.get("errors", [])
            for err in errors:
                category = self.classify_error(err)
                error_counts[category] = error_counts.get(category, 0) + 1
                total_errors_tracked += 1

        # Generate recommendations based on failure occurrences
        recommendations: List[Dict[str, Any]] = []
        for cat, count in error_counts.items():
            if cat == "Missing Authentication":
                recommendations.append({
                    "category": cat,
                    "count": count,
                    "recommendation": "Always enforce JWT token validation and login route protection in prompt specifications."
                })
            elif cat == "Missing Input Validation":
                recommendations.append({
                    "category": cat,
                    "count": count,
                    "recommendation": "Always enforce Pydantic v2 schemas and input sanitization headers."
                })
            elif cat == "Import / Dependency Issue":
                recommendations.append({
                    "category": cat,
                    "count": count,
                    "recommendation": "Ensure requirements.txt and package.json explicitly list all imported third-party modules."
                })
            elif cat == "Database Query Error":
                recommendations.append({
                    "category": cat,
                    "count": count,
                    "recommendation": "Always use parameterized SQL queries and explicit database connection timeout limits."
                })
            else:
                recommendations.append({
                    "category": cat,
                    "count": count,
                    "recommendation": f"Enforce defensive error handling guidelines for category '{cat}'."
                })

        _logger.info(f"FeedbackAnalyzer: Analyzed {total_errors_tracked} errors across {len(experiences)} experiences.")
        return {
            "total_experiences": len(experiences),
            "total_errors_tracked": total_errors_tracked,
            "error_breakdown": error_counts,
            "recommendations": recommendations
        }
