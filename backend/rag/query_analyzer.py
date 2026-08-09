import re
import logging
from typing import Dict, Any, List
from backend.rag.models import DocumentType

logger = logging.getLogger("aiforge.rag.query_analyzer")

# Default DocumentTypes per agent role
AGENT_DOC_TYPES = {
    "planner": [DocumentType.REQUIREMENTS, DocumentType.DOCUMENTATION, DocumentType.USER_GUIDE, DocumentType.PROJECT_MEMORY],
    "architect": [DocumentType.ARCHITECTURE, DocumentType.FRAMEWORK, DocumentType.SECURITY, DocumentType.DATABASE, DocumentType.PROJECT_MEMORY],
    "frontend": [DocumentType.DOCUMENTATION, DocumentType.CODE, DocumentType.API, DocumentType.USER_GUIDE, DocumentType.FRAMEWORK],
    "backend": [DocumentType.FRAMEWORK, DocumentType.API, DocumentType.SECURITY, DocumentType.DATABASE, DocumentType.CODE],
    "database": [DocumentType.DATABASE, DocumentType.CODE, DocumentType.ARCHITECTURE, DocumentType.REQUIREMENTS],
    "reviewer": [DocumentType.CODE, DocumentType.SECURITY, DocumentType.ARCHITECTURE, DocumentType.REQUIREMENTS, DocumentType.DOCUMENTATION],
    "testing": [DocumentType.TEST, DocumentType.REQUIREMENTS, DocumentType.API, DocumentType.CODE],
}

KNOWN_TECHS = {"fastapi", "react", "postgresql", "postgres", "jwt", "stripe", "docker", "python", "javascript", "typescript", "tailwind", "pytest"}


class QueryAnalyzer:
    """
    Analyzes an agent query to determine intent, target technologies, relevant document types, and priority.
    """

    def analyze_query(self, query: str, agent_name: str = "generic") -> Dict[str, Any]:
        q_lower = query.lower()
        agent_key = agent_name.lower()

        # 1. Determine Intent
        intent = "general"
        if any(w in q_lower for w in ["auth", "login", "jwt", "permission", "security"]):
            intent = "authentication"
        elif any(w in q_lower for w in ["database", "schema", "table", "sql", "migration", "postgres"]):
            intent = "database"
        elif any(w in q_lower for w in ["api", "route", "endpoint", "rest", "controller"]):
            intent = "api"
        elif any(w in q_lower for w in ["ui", "component", "page", "view", "css", "layout"]):
            intent = "frontend_ui"
        elif any(w in q_lower for w in ["test", "pytest", "mock", "suite", "assertion"]):
            intent = "testing"

        # 2. Extract Technologies
        techs = [t for t in KNOWN_TECHS if t in q_lower]

        # 3. Determine Document Types based on Agent Role & Intent
        doc_types = list(AGENT_DOC_TYPES.get(agent_key, [DocumentType.DOCUMENTATION, DocumentType.CODE]))
        if intent == "authentication" and DocumentType.SECURITY not in doc_types:
            doc_types.append(DocumentType.SECURITY)
        elif intent == "database" and DocumentType.DATABASE not in doc_types:
            doc_types.append(DocumentType.DATABASE)

        # 4. Priority
        priority = "high" if intent in ("authentication", "database", "api") else "medium"

        analysis = {
            "query": query,
            "agent_name": agent_name,
            "intent": intent,
            "technologies": techs,
            "document_types": [dt.value if isinstance(dt, DocumentType) else str(dt) for dt in doc_types],
            "priority": priority,
        }

        logger.info(f"QueryAnalyzer: agent='{agent_name}' intent='{intent}' techs={techs} doc_types={analysis['document_types']}")
        return analysis


global_query_analyzer = QueryAnalyzer()


def analyze_query(query: str, agent_name: str = "generic") -> Dict[str, Any]:
    return global_query_analyzer.analyze_query(query, agent_name)
