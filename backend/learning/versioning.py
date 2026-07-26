import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.learning.versioning")


class KnowledgeVersioning:
    """
    KnowledgeVersioning tracks revisions and version numbers (v1 -> v2 -> v3)
    for evolving architectural patterns and code templates.
    """

    def bump_version(self, current_version: str) -> str:
        try:
            parts = current_version.split(".")
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return f"{major}.{minor + 1}"
        except Exception:
            return "1.1"


# Global KnowledgeVersioning Instance
global_knowledge_versioning = KnowledgeVersioning()
