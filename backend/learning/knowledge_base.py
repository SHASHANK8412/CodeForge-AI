import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.learning.knowledge_base")


class KnowledgeBase:
    """
    KnowledgeBase stores categorized engineering patterns, confidence scores,
    and architecture templates.
    """

    def __init__(self):
        self.entries: List[Dict[str, Any]] = [
            {
                "id": "kb_01",
                "category": "Architecture",
                "name": "FastAPI + React Microservice Architecture",
                "description": "Production-ready decoupled microservice architecture pattern",
                "confidence_score": 9.8,
                "reuse_count": 42,
                "version": "1.0",
                "tags": ["fastapi", "react", "architecture"]
            },
            {
                "id": "kb_02",
                "category": "Authentication",
                "name": "JWT Auth Dependency Injection",
                "description": "OAuth2 password bearer with JWT token validation",
                "confidence_score": 9.9,
                "reuse_count": 58,
                "version": "1.2",
                "tags": ["jwt", "auth", "security"]
            },
            {
                "id": "kb_03",
                "category": "Database",
                "name": "SQLAlchemy Async Session Pool",
                "description": "Async PostgreSQL connection pool and migration strategy",
                "confidence_score": 9.5,
                "reuse_count": 31,
                "version": "1.0",
                "tags": ["sqlalchemy", "postgres", "database"]
            }
        ]

        self.templates: Dict[str, Dict[str, Any]] = {
            "e_commerce": {
                "name": "E-Commerce Platform",
                "stack": "FastAPI + React + PostgreSQL + Stripe",
                "components": ["Product Catalog", "Cart System", "Checkout Flow", "Order Management"]
            },
            "hospital_management": {
                "name": "Hospital & Healthcare System",
                "stack": "FastAPI + React + PostgreSQL + Docker",
                "components": ["Patient Records", "Doctor Scheduling", "Billing & Claims", "Prescriptions"]
            },
            "banking": {
                "name": "Banking & Fintech System",
                "stack": "FastAPI + React + PostgreSQL + Redis",
                "components": ["Account Ledger", "Fund Transfer", "Audit Logs", "MFA Auth"]
            },
            "chat_app": {
                "name": "Real-time Messaging Platform",
                "stack": "FastAPI WebSockets + React + Redis",
                "components": ["WebSocket Gateway", "Chat Rooms", "Message Store", "Presence Online"]
            }
        }

    def list_knowledge(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists knowledge entries optionally filtered by category."""
        if category:
            return [e for e in self.entries if e.get("category", "").lower() == category.lower()]
        return self.entries

    def store_pattern(self, name: str, category: str, description: str, tags: List[str] = None) -> Dict[str, Any]:
        """Stores a new knowledge item into the KnowledgeBase."""
        entry = {
            "id": f"kb_{len(self.entries) + 1:02d}",
            "category": category,
            "name": name,
            "description": description,
            "confidence_score": 9.0,
            "reuse_count": 1,
            "version": "1.0",
            "tags": tags or [],
            "timestamp": time.time()
        }
        self.entries.append(entry)
        logger.info(f"KnowledgeBase stored pattern '{name}' under '{category}'")
        return entry

    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """Returns architecture template library."""
        return self.templates


# Global KnowledgeBase Instance
global_knowledge_base = KnowledgeBase()
