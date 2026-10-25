"""
AIForge Codebase Intelligence — Change Impact Analyzer
======================================================
Analyzes proposed changes, user requests, or modified files/symbols and determines
the ripple impact across the codebase (routes, components, database models, and test suites).
"""

import logging
from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field

from backend.memory.codebase_indexer import global_codebase_indexer
from backend.memory.dependency_graph import global_dependency_graph

_logger = logging.getLogger("aiforge.memory.impact_analyzer")


class ImpactReport(BaseModel):
    project_id: str
    target_targets: List[str] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)
    affected_routes: List[str] = Field(default_factory=list)
    affected_components: List[str] = Field(default_factory=list)
    affected_models: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    impact_level: str = "LOW"  # CRITICAL, HIGH, MEDIUM, LOW
    summary: str = ""


class ChangeImpactAnalyzer:
    """
    Computes change impact radius using symbol search and dependency graph traversal.
    """

    def __init__(self, indexer=None, dep_graph=None):
        self.indexer = indexer or global_codebase_indexer
        self.dep_graph = dep_graph or global_dependency_graph

    def analyze_change_impact(
        self,
        project_id: str,
        targets: List[str] | str,
        prompt: str = ""
    ) -> ImpactReport:
        """
        Analyzes the impact of modifying target files, symbols, or feature prompt.
        """
        if isinstance(targets, str):
            targets = [targets]

        target_files: Set[str] = set()
        for t in targets:
            clean_t = t.replace("\\", "/").lstrip("/")
            if "/" in clean_t or "." in clean_t:
                target_files.add(clean_t)
            else:
                # Symbol lookup
                matching = self.indexer.find_files_by_symbol(project_id, clean_t)
                target_files.update(matching)

        if prompt and not target_files:
            # Query codebase index for related files
            search_results = self.indexer.search_codebase(project_id, prompt, top_k=5)
            for r in search_results:
                target_files.add(r["path"])

        # Perform transitive dependency graph traversal
        visited: Set[str] = set(target_files)
        queue: List[str] = list(target_files)

        while queue:
            curr = queue.pop(0)
            dependents = self.dep_graph.get_dependents(project_id, curr)
            for dep in dependents:
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)

        # Categorize affected assets
        proj_index = self.indexer.get_project_index(project_id)
        affected_routes: List[str] = []
        affected_components: List[str] = []
        affected_models: List[str] = []
        affected_tests: List[str] = []

        for path in visited:
            meta = proj_index.get(path, {})
            # Routes
            for r in meta.get("routes", []):
                affected_routes.append(f"{r.get('method', 'GET')} {r.get('path', '')}")
            # Components
            for c in meta.get("components", []):
                affected_components.append(c)
            # Models
            for m in meta.get("models", []):
                affected_models.append(m)
            # Tests
            if "test" in path.lower():
                affected_tests.append(path)

        affected_files_list = sorted(list(visited))
        affected_routes = sorted(list(set(affected_routes)))
        affected_components = sorted(list(set(affected_components)))
        affected_models = sorted(list(set(affected_models)))
        affected_tests = sorted(list(set(affected_tests)))

        # Evaluate impact severity
        if len(affected_files_list) >= 8 or len(affected_models) >= 3:
            impact_level = "CRITICAL"
        elif len(affected_files_list) >= 4 or len(affected_routes) >= 2:
            impact_level = "HIGH"
        elif len(affected_files_list) >= 2:
            impact_level = "MEDIUM"
        else:
            impact_level = "LOW"

        summary = (
            f"Impact Analysis: {len(affected_files_list)} file(s) likely affected, "
            f"{len(affected_routes)} API route(s), {len(affected_components)} UI component(s), "
            f"{len(affected_models)} data model(s), {len(affected_tests)} test file(s)."
        )

        _logger.info(f"ChangeImpactAnalyzer for '{project_id}': {summary}")

        return ImpactReport(
            project_id=project_id,
            target_targets=list(targets),
            affected_files=affected_files_list,
            affected_routes=affected_routes,
            affected_components=affected_components,
            affected_models=affected_models,
            affected_tests=affected_tests,
            impact_level=impact_level,
            summary=summary,
        )


# Global ChangeImpactAnalyzer instance
global_impact_analyzer = ChangeImpactAnalyzer()
