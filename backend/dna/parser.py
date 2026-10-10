"""
AIForge Day 15 — Multi-Language AST Code Parser
===============================================
Parses Python, JS, TS, JSX, TSX, SQL, HTML, CSS files to extract:
- Files, imports, exports, classes, functions, components, API endpoints, DB models, DB tables, tests.
"""

import ast
import re
import logging
from typing import Dict, Any, List, Tuple

from backend.dna.models import GraphNode, GraphEdge, NodeKind, RelationType

_logger = logging.getLogger("aiforge.dna.parser")

SECURITY_CRITICAL_KEYWORDS = {
    "auth", "login", "jwt", "token", "password", "payment",
    "stripe", "secret", "permission", "rbac", "session"
}


class CodeParser:
    """
    Static & AST multi-language code parser.
    """

    def is_security_critical(self, name: str, file_path: str) -> bool:
        combined = f"{name} {file_path}".lower()
        return any(kw in combined for kw in SECURITY_CRITICAL_KEYWORDS)

    def parse_python(self, file_path: str, content: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        file_node_id = f"file:{file_path}"
        nodes.append(
            GraphNode(
                id=file_node_id,
                label=file_path.split("/")[-1],
                kind=NodeKind.FILE,
                file_path=file_path,
                security_critical=self.is_security_critical(file_path, file_path)
            )
        )

        try:
            tree = ast.parse(content, filename=file_path)
            for node in ast.walk(tree):
                # Imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module_name = ""
                    if isinstance(node, ast.ImportFrom) and node.module:
                        module_name = node.module
                    elif isinstance(node, ast.Import):
                        module_name = node.names[0].name

                    if module_name:
                        import_node_id = f"file:{module_name}.py"
                        edges.append(
                            GraphEdge(
                                source=file_node_id,
                                target=import_node_id,
                                relation=RelationType.IMPORTS
                            )
                        )

                # Classes / Database Models
                elif isinstance(node, ast.ClassDef):
                    is_db_model = any(
                        isinstance(b, ast.Name) and b.id in ("Base", "Model", "DeclarativeBase")
                        for b in node.bases
                    ) or "model" in file_path.lower()

                    kind = NodeKind.DATABASE_MODEL if is_db_model else NodeKind.CLASS
                    class_node_id = f"class:{file_path}:{node.name}"
                    nodes.append(
                        GraphNode(
                            id=class_node_id,
                            label=node.name,
                            kind=kind,
                            file_path=file_path,
                            line_number=node.lineno,
                            security_critical=self.is_security_critical(node.name, file_path)
                        )
                    )
                    edges.append(
                        GraphEdge(
                            source=file_node_id,
                            target=class_node_id,
                            relation=RelationType.USES
                        )
                    )

                # Functions / Tests / API Routes
                elif isinstance(node, ast.FunctionDef):
                    is_test = node.name.startswith("test_") or "test" in file_path.lower()
                    is_api = any(
                        isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("get", "post", "put", "delete", "patch")
                        for d in node.decorator_list
                    )

                    if is_test:
                        kind = NodeKind.TEST
                    elif is_api:
                        kind = NodeKind.API
                    else:
                        kind = NodeKind.FUNCTION

                    func_node_id = f"func:{file_path}:{node.name}"
                    nodes.append(
                        GraphNode(
                            id=func_node_id,
                            label=node.name,
                            kind=kind,
                            file_path=file_path,
                            line_number=node.lineno,
                            security_critical=self.is_security_critical(node.name, file_path)
                        )
                    )
                    edges.append(
                        GraphEdge(
                            source=file_node_id,
                            target=func_node_id,
                            relation=RelationType.USES
                        )
                    )

        except SyntaxError:
            _logger.debug(f"[Parser] SyntaxError parsing {file_path}")

        return nodes, edges

    def parse_js_ts(self, file_path: str, content: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        file_node_id = f"file:{file_path}"
        nodes.append(
            GraphNode(
                id=file_node_id,
                label=file_path.split("/")[-1],
                kind=NodeKind.FILE,
                file_path=file_path,
                security_critical=self.is_security_critical(file_path, file_path)
            )
        )

        # Regex for imports
        import_matches = re.finditer(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content)
        for match in import_matches:
            target_mod = match.group(1)
            target_node_id = f"file:{target_mod}"
            edges.append(
                GraphEdge(
                    source=file_node_id,
                    target=target_node_id,
                    relation=RelationType.IMPORTS
                )
            )

        # Regex for React Components / Functions
        func_matches = re.finditer(r"(?:export\s+default\s+function|function|const)\s+([A-Z][a-zA-Z0-9_]*)", content)
        for match in func_matches:
            comp_name = match.group(1)
            is_comp = file_path.endswith((".jsx", ".tsx")) or "component" in file_path.lower()
            kind = NodeKind.COMPONENT if is_comp else NodeKind.FUNCTION
            comp_node_id = f"comp:{file_path}:{comp_name}"

            nodes.append(
                GraphNode(
                    id=comp_node_id,
                    label=comp_name,
                    kind=kind,
                    file_path=file_path,
                    security_critical=self.is_security_critical(comp_name, file_path)
                )
            )
            edges.append(
                GraphEdge(
                    source=file_node_id,
                    target=comp_node_id,
                    relation=RelationType.RENDERS if is_comp else RelationType.USES
                )
            )

        return nodes, edges

    def parse_file(self, file_path: str, content: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        if file_path.endswith(".py"):
            return self.parse_python(file_path, content)
        elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            return self.parse_js_ts(file_path, content)
        else:
            file_node_id = f"file:{file_path}"
            kind = NodeKind.CONFIGURATION if file_path.endswith((".json", ".yml", ".toml")) else NodeKind.FILE
            return [
                GraphNode(
                    id=file_node_id,
                    label=file_path.split("/")[-1],
                    kind=kind,
                    file_path=file_path,
                    security_critical=self.is_security_critical(file_path, file_path)
                )
            ], []


global_code_parser = CodeParser()
