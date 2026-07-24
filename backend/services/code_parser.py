"""
AIForge Day 95 AST & Code Parser Service
=========================================
Parses code files (Python, JS, JSX, TSX) to extract functions, classes, imports, routes, components, and dependency symbols.
"""

import ast
import re
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.code_parser")


class CodeParserService:
    """
    Code Parser Service for extracting code entities and AST nodes.
    """

    def parse_python_code(self, code_content: str, filename: str = "main.py") -> Dict[str, Any]:
        _logger.info(f"CodeParserService: Parsing Python file '{filename}'...")

        functions = []
        classes = []
        imports = []
        routes = []

        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                    # Check if decorator specifies a route
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and hasattr(dec.func, 'attr'):
                            routes.append(f"{dec.func.attr} -> {node.name}")
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
        except Exception as e:
            _logger.warning(f"AST parsing warning for '{filename}': {e}")
            # Regex fallback
            functions = re.findall(r"def\s+(\w+)\s*\(", code_content)
            classes = re.findall(r"class\s+(\w+)\s*", code_content)
            imports = re.findall(r"(?:import|from)\s+([a-zA-Z0-9_\.]+)", code_content)

        return {
            "filename": filename,
            "language": "python",
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "routes": routes
        }

    def parse_javascript_code(self, code_content: str, filename: str = "Component.jsx") -> Dict[str, Any]:
        _logger.info(f"CodeParserService: Parsing JS/React file '{filename}'...")

        imports = re.findall(r"import\s+.*?\s+from\s+['\"](.*?)['\"]", code_content)
        functions = re.findall(r"function\s+(\w+)\s*\(", code_content) + re.findall(r"const\s+(\w+)\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>", code_content)
        components = [f for f in functions if f[0].isupper()]

        return {
            "filename": filename,
            "language": "javascript",
            "functions": functions,
            "components": components,
            "imports": imports
        }

    def parse_file(self, code_content: str, filename: str) -> Dict[str, Any]:
        if filename.endswith(".py"):
            return self.parse_python_code(code_content, filename)
        return self.parse_javascript_code(code_content, filename)


global_code_parser = CodeParserService()
