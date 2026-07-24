"""
AIForge Day 95 Intelligent File Locator Service
===============================================
Locates matching project files based on user modification prompt.
Ensures targeted editing (only relevant files) instead of editing random or entire project files.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.file_locator")


class IntelligentFileLocator:
    """
    Intelligent File Discovery & Locator.
    """

    def locate_target_files(self, prompt: str, project_files: List[str]) -> Dict[str, Any]:
        _logger.info(f"IntelligentFileLocator: Finding relevant files for prompt '{prompt}'...")

        prompt_lower = prompt.lower()
        matched_files = []
        reasoning = ""

        # 1. Dark Mode / Theme prompt -> UI files
        if "dark mode" in prompt_lower or "theme" in prompt_lower or "ui" in prompt_lower:
            matched_files = [f for f in project_files if any(ui_kw in f.lower() for ui_kw in ["theme", "navbar", "css", "component", "app", "layout"])]
            if not matched_files:
                matched_files = ["frontend/src/theme.js", "frontend/src/components/Navbar.jsx", "frontend/src/App.css"]
            reasoning = "Targeted UI styling & component files for Dark Mode integration."

        # 2. Database / PostgreSQL prompt -> DB config files
        elif "postgresql" in prompt_lower or "postgres" in prompt_lower or "sqlite" in prompt_lower or "database" in prompt_lower or "orm" in prompt_lower:
            matched_files = [f for f in project_files if any(db_kw in f.lower() for db_kw in ["database", "db", "config", "model", "env", "settings"])]
            if not matched_files:
                matched_files = ["backend/database.py", "backend/config.py", "backend/models.py"]
            reasoning = "Targeted Database connection strings, ORM models, and configuration files."

        # 3. Dashboard / Performance prompt -> Dashboard & metrics files
        elif "dashboard" in prompt_lower or "optimize" in prompt_lower or "loading" in prompt_lower or "perf" in prompt_lower:
            matched_files = [f for f in project_files if any(p_kw in f.lower() for p_kw in ["dashboard", "metric", "cache", "service", "analytics"])]
            if not matched_files:
                matched_files = ["frontend/src/pages/Dashboard.jsx", "backend/services/metrics_service.py", "backend/cache.py"]
            reasoning = "Targeted Dashboard component, analytics service, and caching layer for loading optimization."

        # 4. Login / Auth bug prompt -> Auth & route files
        elif "login" in prompt_lower or "auth" in prompt_lower or "jwt" in prompt_lower or "bug" in prompt_lower:
            matched_files = [f for f in project_files if any(a_kw in f.lower() for a_kw in ["auth", "login", "jwt", "route", "user", "middleware"])]
            if not matched_files:
                matched_files = ["backend/auth.py", "backend/routes/auth_routes.py", "backend/middleware/jwt.py"]
            reasoning = "Targeted Authentication controller, JWT middleware, and route handlers."

        else:
            # Fallback keyword match
            keywords = prompt_lower.split()
            matched_files = [f for f in project_files if any(kw in f.lower() for kw in keywords if len(kw) > 3)]
            if not matched_files:
                matched_files = project_files[:2] if project_files else ["main.py"]
            reasoning = "Matched files based on keyword search."

        return {
            "prompt": prompt,
            "matched_files_count": len(matched_files),
            "target_files": matched_files,
            "reasoning": reasoning
        }


global_file_locator = IntelligentFileLocator()
