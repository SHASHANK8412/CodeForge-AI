"""
AIForge Memory Indexer Service (Day 44)
=======================================
Indexes projects, errors, solutions, components, prompts, and architecture into long-term memory collections with rich metadata.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.memory_indexer")


class MemoryIndexer:
    """
    Indexes extracted knowledge into persistent long-term memory stores.
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        _root = Path(__file__).resolve().parent.parent.parent
        self.memory_dir = memory_dir or (_root / "backend" / "memory")
        self.projects_dir = self.memory_dir / "projects"
        self.patterns_dir = self.memory_dir / "patterns"
        self.solutions_dir = self.memory_dir / "solutions"
        self.metrics_dir = self.memory_dir / "metrics"
        self._ensure_directories()

    def _ensure_directories(self):
        for d in [self.projects_dir, self.patterns_dir, self.solutions_dir, self.metrics_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def index_project(
        self,
        project_id: str,
        prompt: str,
        knowledge: Dict[str, Any],
        quality_score: float = 95.0,
        framework: str = "FullStack"
    ) -> Dict[str, Any]:
        """
        Indexes a completed project into long-term memory stores with rich metadata tags.
        """
        record = {
            "project_id": project_id,
            "prompt": prompt,
            "framework": framework,
            "quality_score": quality_score,
            "tags": list(set(prompt.lower().split() + [framework.lower()])),
            "knowledge": knowledge,
            "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # Save project memory file
        p_file = self.projects_dir / f"{project_id}.json"
        p_file.write_text(json.dumps(record, indent=2), encoding="utf-8")

        # Index components & solutions
        for comp in knowledge.get("ui_components", []):
            c_file = self.patterns_dir / f"comp_{int(time.time() * 1000)}.json"
            c_file.write_text(json.dumps(comp, indent=2), encoding="utf-8")

        for fix in knowledge.get("error_resolution_pairs", []):
            s_file = self.solutions_dir / f"sol_{int(time.time() * 1000)}.json"
            s_file.write_text(json.dumps(fix, indent=2), encoding="utf-8")

        _logger.info(f"MemoryIndexer: Indexed project '{project_id}' into long-term memory.")
        return record


global_memory_indexer = MemoryIndexer()
