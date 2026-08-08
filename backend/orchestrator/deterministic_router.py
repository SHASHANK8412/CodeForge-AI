"""
AIForge Deterministic Router
=============================
Zero-LLM latency requirement analyzer and tech stack router.
Parses user prompt using pattern matching and keyword heuristics to instantly
determine project requirements, tech stack (Frontend/Backend/DB), authentication,
containerization, and external APIs.
"""

import re
from typing import Dict, Any, List

class DeterministicRouter:
    """
    Rule-based router that avoids unnecessary LLM latency for task routing & stack selection.
    """

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower()

        # Project Name Extraction
        proj_name = "aiforge-app"
        name_match = re.search(r'(?:build|create|make|generate)\s+(?:a|an)?\s*([a-z0-9_\-\s]+?)\s+(?:app|application|system|service|tracker|tool|platform)', p_lower)
        if name_match:
            clean_name = re.sub(r'[^a-z0-9\-]', '-', name_match.group(1).strip())
            proj_name = clean_name.strip('-') or "aiforge-app"

        # Tech Stack Detection
        frontend = "react"
        if "vue" in p_lower:
            frontend = "vue"
        elif "next" in p_lower or "nextjs" in p_lower:
            frontend = "nextjs"
        elif "html" in p_lower or "vanilla" in p_lower:
            frontend = "vanilla_html"

        backend = "fastapi"
        if "express" in p_lower or "node" in p_lower:
            backend = "express"
        elif "flask" in p_lower:
            backend = "flask"
        elif "django" in p_lower:
            backend = "django"

        database = "postgresql"
        if "sqlite" in p_lower:
            database = "sqlite"
        elif "mongo" in p_lower or "mongodb" in p_lower:
            database = "mongodb"
        elif "redis" in p_lower:
            database = "redis"

        # Feature flags
        has_auth = any(kw in p_lower for kw in ["auth", "login", "jwt", "session", "user", "signup", "register"])
        has_docker = any(kw in p_lower for kw in ["docker", "container", "dockerfile", "docker-compose"])
        has_realtime = any(kw in p_lower for kw in ["websocket", "socket.io", "realtime", "chat", "live"])
        has_rag = any(kw in p_lower for kw in ["rag", "vector", "embedding", "chroma", "llm", "ai"])

        return {
            "project_name": proj_name,
            "frontend": frontend,
            "backend": backend,
            "database": database,
            "features": {
                "auth": has_auth,
                "docker": has_docker,
                "realtime": has_realtime,
                "rag": has_rag,
            },
            "routing_type": "DETERMINISTIC",
            "latency_ms": 0.0
        }

global_deterministic_router = DeterministicRouter()
