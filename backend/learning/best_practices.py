"""
AIForge Engineering Best Practices Store & Generator
===================================================
Maintains global best practices in memory/best_practices.json and learning/knowledge/best_practices.md.
Provides actionable rules for agent prompt injection and quality validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning")


class BestPracticesGenerator:
    """
    Extracts and stores engineering best practices across project generations.
    """

    def __init__(self, memory_dir: Optional[str] = None, knowledge_dir: Optional[str] = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).resolve().parents[1] / "memory")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.memory_dir / "best_practices.json"
        
        if knowledge_dir is None:
            self.knowledge_dir = Path(__file__).resolve().parent / "knowledge"
        else:
            self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.md_path = self.knowledge_dir / "best_practices.md"

        self._init_defaults()

    def _init_defaults(self) -> None:
        if not self.json_path.exists() or self.json_path.stat().st_size == 0:
            defaults = [
                {"id": "bp_1", "rule": "Always enforce JWT token authentication and expiration limits on protected endpoints."},
                {"id": "bp_2", "rule": "Always validate inputs using Pydantic v2 schemas and sanitize request payloads."},
                {"id": "bp_3", "rule": "Always parameterize SQL queries to prevent SQL injection vulnerabilities."},
                {"id": "bp_4", "rule": "Always restrict CORS headers to explicit trusted origin domains."},
                {"id": "bp_5", "rule": "Always include pagination parameters (limit & offset) on database list queries."},
                {"id": "bp_6", "rule": "Always cache expensive API endpoints using Redis or LRU memory caches."},
                {"id": "bp_7", "rule": "Always write automated unit tests for core backend services and route controllers."},
                {"id": "bp_8", "rule": "Always generate Docker multi-stage build files with a non-root appuser."}
            ]
            self._save_json(defaults)

        if not self.md_path.exists():
            default_md = """# AIForge Master Engineering Best Practices

Master guidelines compiled across project builds.

## 1. Authentication & Security
* Enforce JWT token validation on protected API endpoints.
* Sanitize all inputs and restrict CORS access.

## 2. API Design & Database
* Use asynchronous route controllers (FastAPI).
* Parameterize SQL queries and enforce pagination limits.

## 3. DevOps & Testing
* Maintain automated Pytest verification suites.
* Use multi-stage Docker build files with non-root user execution.
"""
            try:
                with open(self.md_path, "w", encoding="utf-8") as f:
                    f.write(default_md)
            except Exception as e:
                _logger.error(f"Failed to write default best_practices.md: {e}")

    def _load_json(self) -> List[Dict[str, Any]]:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _logger.error(f"Failed to load best_practices.json: {e}")
            return []

    def _save_json(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save best_practices.json: {e}")

    def add_best_practice(self, rule: str) -> Dict[str, Any]:
        practices = self._load_json()
        # Avoid duplicate rules
        for p in practices:
            if p.get("rule", "").lower() == rule.lower():
                return p

        new_bp = {
            "id": f"bp_{len(practices) + 1}",
            "rule": rule
        }
        practices.append(new_bp)
        self._save_json(practices)

        # Append to markdown documentation
        try:
            with open(self.md_path, "a", encoding="utf-8") as f:
                f.write(f"\n* {rule}\n")
        except Exception as e:
            _logger.error(f"Failed to append to best_practices.md: {e}")

        _logger.info(f"BestPracticesGenerator: Recorded new best practice '{rule}'")
        return new_bp

    def get_all_best_practices(self) -> List[Dict[str, Any]]:
        return self._load_json()

    def update_best_practices(self, project_summary: Dict[str, Any]) -> str:
        """
        Extracts new best practices from project summary and updates storage.
        """
        techs = project_summary.get("technologies", [])
        practices = project_summary.get("best_practices", {})
        
        sec_practices = practices.get("security_practices", [])
        for sec in sec_practices:
            if len(sec) > 1:
                self.add_best_practice(sec)

        project_name = project_summary.get("project", "Generic Project")
        score = project_summary.get("final_score", 90)
        insight_block = f"\n\n## Project Insight: {project_name}\n* **Technologies**: {', '.join(techs)}\n* **Score**: {score}%\n"

        try:
            with open(self.md_path, "a", encoding="utf-8") as f:
                f.write(insight_block)
        except Exception as e:
            _logger.error(f"Failed to append project insight to best_practices.md: {e}")

        return self.md_path.read_text(encoding="utf-8") if self.md_path.exists() else ""
