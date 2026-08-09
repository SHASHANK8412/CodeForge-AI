"""
AIForge Production Knowledge Store & Bug Memory
==============================================
Manages Bug Memory, Best Practice Libraries, and Knowledge Ranking (Quality Score, Usage Count, Failure Count, Success Rate, Confidence Score).
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.knowledge_store")


class ProductionKnowledgeStore:
    """
    Stores bug memories, best practices, and knowledge rankings.
    """

    def __init__(self) -> None:
        self.bugs: Dict[str, Dict[str, Any]] = {
            "bug_db_timeout": {
                "bug_id": "bug_db_timeout",
                "bug": "Database Connection Timeout under Load",
                "cause": "Exhausted SQLAlchemy connection pool",
                "solution": "Increase pool_size to 20 and add pool_pre_ping=True",
                "affected_files": ["backend/database.py"],
                "confidence_score": 0.96,
                "usage_count": 14,
                "failure_count": 0,
                "quality_score": 98.0,
                "success_rate": 100.0,
                "ranking": 1,
                "recorded_at": time.time() - 86400
            }
        }

        self.best_practices: Dict[str, Dict[str, Any]] = {
            "folder_structure": {
                "category": "Folder Structures",
                "title": "Clean FastAPI + React Monorepo Layout",
                "content": "backend/ (agents, routes, models), frontend/ (src/components, src/pages), Dockerfile",
                "quality_score": 96.0
            },
            "api_design": {
                "category": "API Design",
                "title": "RESTful URI Path Versioning",
                "content": "Use /api/v1/ prefix with explicit HTTP verb semantics",
                "quality_score": 98.0
            },
            "authentication": {
                "category": "Authentication",
                "title": "JWT Bearer Token Security",
                "content": "OAuth2 Password Bearer with 15-minute access token and 7-day refresh token",
                "quality_score": 99.0
            },
            "database_design": {
                "category": "Database Design",
                "title": "PostgreSQL Indexing & WAL Retention",
                "content": "B-tree unique indexes on user emails and automated daily WAL snapshots",
                "quality_score": 95.0
            },
            "docker": {
                "category": "Docker",
                "title": "Multi-Stage Slim Build",
                "content": "Python alpine base image with multi-stage layer caching",
                "quality_score": 97.0
            }
        }

    def record_bug_fix(
        self,
        bug: str,
        cause: str,
        solution: str,
        affected_files: List[str],
        confidence_score: float = 0.95
    ) -> Dict[str, Any]:
        bug_key = bug.lower().replace(" ", "_")
        if bug_key in self.bugs:
            b = self.bugs[bug_key]
            b["usage_count"] += 1
            b["success_rate"] = round((b["usage_count"] / max(1, b["usage_count"] + b["failure_count"])) * 100, 1)
            b["confidence_score"] = round(min(0.99, b["confidence_score"] + 0.01), 2)
            _logger.info(f"ProductionKnowledgeStore: Incremented usage for bug fix '{bug}' (Usage: {b['usage_count']})")
            return b
        else:
            bug_id = f"bug_{int(time.time() * 1000)}"
            entry = {
                "bug_id": bug_id,
                "bug": bug,
                "cause": cause,
                "solution": solution,
                "affected_files": affected_files,
                "confidence_score": confidence_score,
                "usage_count": 1,
                "failure_count": 0,
                "quality_score": round(confidence_score * 100, 1),
                "success_rate": 100.0,
                "ranking": len(self.bugs) + 1,
                "recorded_at": time.time()
            }
            self.bugs[bug_key] = entry
            _logger.info(f"ProductionKnowledgeStore: Recorded new bug fix '{bug}'")
            return entry

    def find_matching_bug_solution(self, bug_description: str) -> Optional[Dict[str, Any]]:
        desc_lower = bug_description.lower()
        for b in self.bugs.values():
            if any(term in desc_lower for term in b["bug"].lower().split()):
                _logger.info(f"ProductionKnowledgeStore: Found matching solution for '{bug_description}' -> {b['solution']}")
                return b
        return None

    def get_all_bugs(self) -> List[Dict[str, Any]]:
        return sorted(list(self.bugs.values()), key=lambda b: b["quality_score"], reverse=True)

    def get_best_practices(self) -> List[Dict[str, Any]]:
        return list(self.best_practices.values())


global_production_knowledge_store = ProductionKnowledgeStore()
