"""
AIForge Codebase Intelligence — Lightweight Dependency Graph Engine
====================================================================
Maps and tracks structural relationships across project files:
IMPORTS, CALLS, ROUTES_TO, USES, EXTENDS, and DEPENDS_ON.
Enables change impact analysis and architectural validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

_logger = logging.getLogger("aiforge.memory.dependency_graph")


class CodeDependencyGraph:
    """
    Lightweight in-memory and file-backed code dependency graph.
    """

    def __init__(self, store_path: Optional[str] = None):
        if store_path is None:
            data_dir = Path(__file__).resolve().parent / "store"
            data_dir.mkdir(parents=True, exist_ok=True)
            store_path = str(data_dir / "dependency_graphs.json")
        self.store_file = Path(store_path)
        self._graphs: Dict[str, Dict[str, Any]] = {}  # { project_id: { "nodes": [], "edges": [] } }
        self._load()

    def _load(self) -> None:
        if self.store_file.exists():
            try:
                raw = json.loads(self.store_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._graphs = raw
            except Exception as e:
                _logger.warning(f"Could not load dependency graph: {e}")
                self._graphs = {}

    def _save(self) -> None:
        try:
            self.store_file.parent.mkdir(parents=True, exist_ok=True)
            self.store_file.write_text(json.dumps(self._graphs, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"Could not save dependency graph: {e}")

    def build_graph_from_index(self, project_id: str, project_index: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds nodes and directed edges from codebase index metadata.
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        edge_set: Set[str] = set()

        for path, meta in project_index.items():
            nodes.append({
                "id": path,
                "label": path.split("/")[-1],
                "language": meta.get("language", "text"),
                "type": "file",
                "symbols": meta.get("symbols", []),
            })

            imports = meta.get("imports", [])
            for imp in imports:
                # Find matching target files in the project
                for target_path, target_meta in project_index.items():
                    if target_path == path:
                        continue
                    stem = target_path.split("/")[-1].rsplit(".", 1)[0]
                    clean_target = target_path.replace("/", ".").rsplit(".", 1)[0]

                    if imp == stem or imp.endswith(f".{stem}") or imp in clean_target or stem in imp:
                        edge_key = f"{path}->IMPORTS->{target_path}"
                        if edge_key not in edge_set:
                            edge_set.add(edge_key)
                            edges.append({
                                "source": path,
                                "target": target_path,
                                "relationship": "IMPORTS",
                            })

            # Check test dependencies (e.g. tests/test_products.py depends on backend/routes/products.py)
            if "test" in path.lower():
                for target_path in project_index.keys():
                    if target_path == path:
                        continue
                    stem = target_path.split("/")[-1].rsplit(".", 1)[0]
                    if stem in path.lower() or stem in meta.get("symbols", []):
                        edge_key = f"{path}->DEPENDS_ON->{target_path}"
                        if edge_key not in edge_set:
                            edge_set.add(edge_key)
                            edges.append({
                                "source": path,
                                "target": target_path,
                                "relationship": "DEPENDS_ON",
                            })

            # Check frontend API to backend route linkages (ROUTES_TO)
            if "api" in path.lower() or "service" in path.lower() or "component" in path.lower():
                for target_path, target_meta in project_index.items():
                    if "route" in target_path.lower() or "main.py" in target_path.lower():
                        target_routes = target_meta.get("routes", [])
                        for r in target_routes:
                            route_stem = r.get("path", "").strip("/").split("/")[0]
                            if route_stem and route_stem in path.lower():
                                edge_key = f"{path}->ROUTES_TO->{target_path}"
                                if edge_key not in edge_set:
                                    edge_set.add(edge_key)
                                    edges.append({
                                        "source": path,
                                        "target": target_path,
                                        "relationship": "ROUTES_TO",
                                    })

        graph_data = {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

        self._graphs[project_id] = graph_data
        self._save()
        _logger.info(f"DependencyGraph for '{project_id}': Built {len(nodes)} nodes and {len(edges)} edges")
        return graph_data

    def get_graph(self, project_id: str) -> Dict[str, Any]:
        """Returns the dependency graph for a project."""
        return self._graphs.get(project_id, {"nodes": [], "edges": []})

    def get_dependencies(self, project_id: str, file_path: str) -> List[str]:
        """Returns list of files that file_path directly depends on / imports."""
        graph = self.get_graph(project_id)
        clean_p = file_path.replace("\\", "/").lstrip("/")
        return [e["target"] for e in graph.get("edges", []) if e.get("source") == clean_p]

    def get_dependents(self, project_id: str, file_path: str) -> List[str]:
        """Returns list of files that depend on / import file_path."""
        graph = self.get_graph(project_id)
        clean_p = file_path.replace("\\", "/").lstrip("/")
        return [e["source"] for e in graph.get("edges", []) if e.get("target") == clean_p]


# Global CodeDependencyGraph instance
global_dependency_graph = CodeDependencyGraph()
