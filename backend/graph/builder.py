"""
AIForge Project Knowledge Graph Builder
=======================================
Scans workspace codebase and constructs a NetworkX Directed Graph (DiGraph).
Captures nodes (Files, Classes, Functions, APIs, DB Tables, Components, Env Vars, Dependencies)
and directed relationships (IMPORTS, CONTAINS, DEFINES_ROUTE, QUERIES_TABLE, USES_ENV, DEPENDS_ON).
Saves project knowledge graph to memory/project_graph.json.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import networkx as nx

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.graph.parser import CodebaseParser
from backend.memory.graph_memory import GraphMemory

_logger = logging.getLogger("aiforge.graph")


class GraphBuilder:
    """
    Constructs and persists the Project Knowledge Graph using NetworkX.
    """

    def __init__(self, workspace_path: Optional[str] = None) -> None:
        if workspace_path is None:
            workspace_path = str(project_root)
        self.workspace_root = Path(workspace_path)
        self.parser = CodebaseParser()
        self.memory = GraphMemory()

    def build_graph(self) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Scans codebase directory and constructs NetworkX DiGraph.
        """
        _logger.info(f"GraphBuilder: Scanning codebase at '{self.workspace_root}'...")
        G = nx.DiGraph()

        scanned_files = 0
        total_functions = 0
        total_classes = 0
        total_apis = 0
        total_db_models = 0
        total_env_vars = 0
        total_dependencies = 0

        # Walk directory
        for current_root, dirs, files in os.walk(self.workspace_root):
            # Exclude cache and hidden folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules", "dist", "build", ".venv", "venv"]]
            for file_name in files:
                file_path = Path(current_root) / file_name
                # Only scan code & config files
                if file_name.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".txt")) or file_name in ["Dockerfile", "docker-compose.yml"]:
                    scanned_files += 1
                    parsed_info = self.parser.scan_file(file_path, self.workspace_root)
                    f_node = parsed_info["file_path"]

                    # Add file node
                    G.add_node(f_node, node_type="file", ext=parsed_info["ext"])

                    # 1. Classes
                    for cls in parsed_info["classes"]:
                        total_classes += 1
                        cls_node = f"Class:{cls}"
                        G.add_node(cls_node, node_type="class", name=cls, file=f_node)
                        G.add_edge(f_node, cls_node, relation="CONTAINS")

                    # 2. Functions
                    for func in parsed_info["functions"]:
                        total_functions += 1
                        func_node = f"Function:{func}"
                        G.add_node(func_node, node_type="function", name=func, file=f_node)
                        G.add_edge(f_node, func_node, relation="CONTAINS")

                    # 3. APIs
                    for api in parsed_info["apis"]:
                        total_apis += 1
                        api_node = f"API:{api['method']} {api['endpoint']}"
                        G.add_node(api_node, node_type="api", method=api["method"], endpoint=api["endpoint"], file=f_node)
                        G.add_edge(f_node, api_node, relation="DEFINES_ROUTE")

                    # 4. DB Tables
                    for tbl in parsed_info["db_tables"]:
                        total_db_models += 1
                        tbl_node = f"Table:{tbl}"
                        G.add_node(tbl_node, node_type="database_model", name=tbl, file=f_node)
                        G.add_edge(f_node, tbl_node, relation="QUERIES_TABLE")

                    # 5. Env Vars
                    for env in parsed_info["env_vars"]:
                        total_env_vars += 1
                        env_node = f"Env:{env}"
                        G.add_node(env_node, node_type="environment_variable", name=env)
                        G.add_edge(f_node, env_node, relation="USES_ENV")

                    # 6. Dependencies
                    for dep in parsed_info["dependencies"]:
                        total_dependencies += 1
                        dep_node = f"Dep:{dep}"
                        G.add_node(dep_node, node_type="dependency", name=dep)
                        G.add_edge(f_node, dep_node, relation="DEPENDS_ON")

                    # 7. Imports (File-to-File / Module edge)
                    for imp in parsed_info["imports"]:
                        G.add_edge(f_node, f"Module:{imp}", relation="IMPORTS")

        summary = {
            "total_files": scanned_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_apis": total_apis,
            "total_db_models": total_db_models,
            "total_env_vars": total_env_vars,
            "total_dependencies": total_dependencies,
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges()
        }

        # Save to memory
        self.memory.save_graph(G, summary=summary)
        _logger.info(f"GraphBuilder: Complete! {scanned_files} Files, {total_functions} Functions, {total_classes} Classes, {total_apis} APIs, {total_db_models} DB Models.")
        return G, summary


def main():
    builder = GraphBuilder()
    print("\nScanning project...")
    G, summary = builder.build_graph()
    print(f"\n{summary['total_files']} Files")
    print(f"{summary['total_functions']} Functions")
    print(f"{summary['total_classes']} Classes")
    print(f"{summary['total_apis']} APIs")
    print(f"{summary['total_db_models']} Database Models")
    print(f"{summary['total_nodes']} Total Nodes")
    print(f"{summary['total_edges']} Total Edges")
    print("\nKnowledge Graph Created")
    print(f"Saved project_graph.json\n")


if __name__ == "__main__":
    main()
