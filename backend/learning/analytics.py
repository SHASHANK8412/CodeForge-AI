import logging
from typing import Dict, Any

from backend.learning.knowledge_base import global_knowledge_base

logger = logging.getLogger("aiforge.learning.analytics")


class LearningAnalytics:
    """
    LearningAnalytics aggregates continuous learning metrics: projects learned,
    total knowledge entries, patterns reused, and average retrieval speed.
    """

    def get_analytics(self) -> Dict[str, Any]:
        entries = global_knowledge_base.list_knowledge()
        templates = global_knowledge_base.get_templates()
        total_reuse = sum(e.get("reuse_count", 0) for e in entries)
        scored = [e["confidence_score"] for e in entries if isinstance(e.get("confidence_score"), (int, float))]
        projects = {e.get(k) for e in entries for k in ("project_id", "source_project") if e.get(k)}

        return {
            "projects_learned": len(projects),
            "total_knowledge_entries": len(entries),
            "total_patterns_reused": total_reuse,
            "architecture_templates": len(templates),
            "average_confidence_score": round(sum(scored) / len(scored), 1) if scored else None,
            "average_retrieval_time_ms": None,     # not measured
            "learning_accuracy_percent": None,     # no accuracy evaluation exists
        }


# Global LearningAnalytics Instance
global_learning_analytics = LearningAnalytics()
