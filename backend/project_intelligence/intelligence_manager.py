import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from .dependency_scanner import DependencyScanner
from .file_summarizer import FileSummarizer
from .api_mapper import ApiMapper
from .schema_inferer import SchemaInferer
from .component_mapper import ComponentMapper
from .impact_analyzer import ImpactAnalyzer
from .smell_detector import SmellDetector

_logger = logging.getLogger("aiforge.project_intelligence")

class ProjectIntelligenceManager:
    """
    Main coordinator implementing SRE Day 37 Project Intelligence Scans.
    """

    def __init__(self, workspace_path: str, memory_path: str = None) -> None:
        self.workspace_path = Path(workspace_path)
        if memory_path is None:
            self.memory_path = self.workspace_path / "backend" / "project_intelligence" / "memory"
        else:
            self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)

        self.dep_scanner = DependencyScanner()
        self.file_summarizer = FileSummarizer()
        self.api_mapper = ApiMapper()
        self.schema_inferer = SchemaInferer()
        self.component_mapper = ComponentMapper()
        self.impact_analyzer = ImpactAnalyzer()
        self.smell_detector = SmellDetector()

    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Coordinates full scan pipeline, updating the 7 project memory files.
        """
        _logger.info("Starting Full SRE Project Analysis...")
        
        # 1. Dependency Graph
        dep_graph = self.dep_scanner.scan_project(str(self.workspace_path))
        self._save_json("dependency_graph.json", dep_graph)

        # 2. Project Graph (nodes & edges layout representing imports)
        nodes = [{"id": f} for f in dep_graph]
        edges = []
        for src, dests in dep_graph.items():
            for dest in dests:
                edges.append({"source": src, "target": dest})
        project_graph = {"nodes": nodes, "links": edges}
        self._save_json("project_graph.json", project_graph)

        # 3. Component Tree
        component_tree = self.component_mapper.build_tree(str(self.workspace_path))
        self._save_json("component_tree.json", component_tree)

        # 4. API Map
        api_map = self.api_mapper.map_apis(str(self.workspace_path))
        self._save_json("api_map.json", api_map)

        # 5. Schema relationships & Architecture summary
        schema_info = self.schema_inferer.infer_relationships(str(self.workspace_path))
        architecture_info = {
            "database_tables": schema_info["tables"],
            "database_relationships": schema_info["relationships"],
            "frameworks_detected": ["FastAPI", "React", "Docker"],
            "architectural_style": "MVC / SPA / Microservices ready"
        }
        self._save_json("architecture.json", architecture_info)

        # 6. Change Impact Analysis
        impact_map = {}
        for f in dep_graph:
            impact_map[f] = self.impact_analyzer.analyze_impact(dep_graph, f)
        self._save_json("impact_analysis.json", impact_map)

        # 7. Quality smells / Dead Code Report
        smells = self.smell_detector.scan_smells(str(self.workspace_path))
        self._save_json("dead_code_report.json", smells)

        _logger.info("Project Intelligence Analysis Complete.")
        return {
            "dependency_graph": dep_graph,
            "project_graph": project_graph,
            "component_tree": component_tree,
            "api_map": api_map,
            "architecture": architecture_info,
            "impact_analysis": impact_map,
            "dead_code_report": smells
        }

    def _save_json(self, filename: str, data: Any) -> None:
        target = self.memory_path / filename
        try:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            _logger.info(f"Saved intelligence registry file: {filename}")
        except Exception as e:
            _logger.error(f"Failed to save {filename}: {str(e)}")
