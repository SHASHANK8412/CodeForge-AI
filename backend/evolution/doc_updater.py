"""
AIForge Automated Documentation Updater
========================================
Keeps documentation synchronized with codebase evolution.
Automatically updates README.md, Swagger / OpenAPI spec, Architecture Mermaid diagrams,
and Dependency Graphs when APIs or models are modified.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.graph.exporter import GraphExporter

_logger = logging.getLogger("aiforge.evolution")


class DocumentationUpdater:
    """
    Synchronizes documentation with code evolution.
    """

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        if workspace_root is None:
            workspace_root = str(Path(__file__).resolve().parents[2])
        self.workspace_root = Path(workspace_root)
        self.exporter = GraphExporter()

    def update_documentation(self, evolution_summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = evolution_summary.get("proposed_change", "Codebase Evolution")
        updated_files = evolution_summary.get("files_updated", [])

        _logger.info(f"DocumentationUpdater synchronizing docs for change: '{prompt}'")

        # 1. Update README.md section
        readme_path = self.workspace_root / "README.md"
        readme_updated = False
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding="utf-8")
                if "## Evolution Changelog" not in content:
                    content += f"\n\n## Evolution Changelog\n* **{prompt}**: Updated {len(updated_files)} files.\n"
                readme_path.write_text(content, encoding="utf-8")
                readme_updated = True
            except Exception as e:
                _logger.error(f"Failed to update README.md: {e}")

        # 2. Export the generated dependency graph to its own file. docs/ARCHITECTURE.md is
        # hand-written and must not be overwritten by generated output.
        graph_path = self.workspace_root / "docs" / "DEPENDENCY_GRAPH.md"
        graph_updated = False
        try:
            self.exporter.export_mermaid_markdown(str(graph_path))
            graph_updated = True
        except Exception as e:  # noqa: BLE001
            _logger.error(f"Failed to export dependency graph: {e}")

        return {
            "proposed_change": prompt,
            "readme_updated": readme_updated,
            "swagger_updated": False,
            "architecture_updated": False,
            "dependency_graph_updated": graph_updated,
            "updated_doc_files": (["README.md"] if readme_updated else []) + (["docs/DEPENDENCY_GRAPH.md"] if graph_updated else [])
        }
