"""
AIForge Workspace Analytics & Cross-Project Knowledge Sharing
============================================================
Tracks cross-project code patterns, extracted architectural insights, reusable modules, and shared knowledge bases.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.workspace.analytics")


class WorkspaceAnalytics:
    """
    Manages knowledge pattern extraction, cross-project sharing, and portfolio analytics.
    """

    def __init__(self) -> None:
        self.knowledge_base: Dict[str, Dict[str, Any]] = {
            "jwt_auth": {
                "pattern_id": "jwt_auth",
                "title": "JWT Authentication Package",
                "category": "Security / Auth",
                "origin_project": "Hospital Management",
                "reused_count": 3,
                "reused_in_projects": ["Ecommerce Platform", "CRM System", "Banking Platform"],
                "description": "Standardized JWT token generation, verification, and HTTP bearer middleware.",
                "created_at": time.time() - 86400
            },
            "react_login": {
                "pattern_id": "react_login",
                "title": "React Auth & Login Component",
                "category": "Frontend UI",
                "origin_project": "Ecommerce Platform",
                "reused_count": 2,
                "reused_in_projects": ["CRM System", "Banking Platform"],
                "description": "Reusable login screen with state management, form validation, and dark mode support.",
                "created_at": time.time() - 43200
            }
        }

    def register_pattern(
        self,
        pattern_id: str,
        title: str,
        category: str,
        origin_project: str,
        description: str,
        code_snippet: Optional[str] = None
    ) -> Dict[str, Any]:
        pattern = {
            "pattern_id": pattern_id,
            "title": title,
            "category": category,
            "origin_project": origin_project,
            "reused_count": 0,
            "reused_in_projects": [],
            "description": description,
            "code_snippet": code_snippet or "",
            "created_at": time.time()
        }
        self.knowledge_base[pattern_id] = pattern
        _logger.info(f"WorkspaceAnalytics: Registered pattern '{title}' from project '{origin_project}'")
        return pattern

    def reuse_pattern(self, pattern_id: str, target_project: str) -> Dict[str, Any]:
        if pattern_id in self.knowledge_base:
            pattern = self.knowledge_base[pattern_id]
            if target_project not in pattern["reused_in_projects"]:
                pattern["reused_in_projects"].append(target_project)
                pattern["reused_count"] += 1
            _logger.info(f"WorkspaceAnalytics: Pattern '{pattern['title']}' reused in '{target_project}'")
            return {
                "status": "success",
                "pattern": pattern,
                "target_project": target_project
            }
        raise ValueError(f"Pattern ID '{pattern_id}' not found in knowledge base.")

    def get_knowledge_base(self) -> List[Dict[str, Any]]:
        return list(self.knowledge_base.values())

    def get_all_patterns(self) -> List[Dict[str, Any]]:
        return list(self.knowledge_base.values())

    def get_analytics_summary(self) -> Dict[str, Any]:
        total_patterns = len(self.knowledge_base)
        total_reuses = sum(p["reused_count"] for p in self.knowledge_base.values())
        return {
            "total_shared_patterns": total_patterns,
            "total_cross_project_reuses": total_reuses,
            "top_reused_patterns": sorted(self.knowledge_base.values(), key=lambda p: p["reused_count"], reverse=True),
            "knowledge_base": list(self.knowledge_base.values())
        }


global_workspace_analytics = WorkspaceAnalytics()
