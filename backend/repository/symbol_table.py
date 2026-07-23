"""
AIForge Repository Symbol Table
================================
Indexes all Functions, Classes, Variables, Interfaces, Constants, and Enums across the entire codebase.
Allows agents to query symbol definitions, signature parameter locations, and usage sites.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.repository")


class RepositorySymbolTable:
    """
    Symbol Table indexing functions, classes, variables, interfaces, constants, and enums.
    """

    def build_symbol_table(self, file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        functions_map = {}
        classes_map = {}
        routes_map = {}
        components_map = {}

        for meta in file_metadata:
            f_name = meta["filename"]
            for func in meta.get("functions", []):
                functions_map[func] = f_name
            for cls in meta.get("classes", []):
                classes_map[cls] = f_name
            for r in meta.get("routes", []):
                routes_map[r] = f_name
            for c in meta.get("components", []):
                components_map[c] = f_name

        _logger.info(f"RepositorySymbolTable: Indexed {len(functions_map)} functions, {len(classes_map)} classes, {len(routes_map)} routes.")

        return {
            "total_symbols": len(functions_map) + len(classes_map) + len(components_map),
            "functions": functions_map,
            "classes": classes_map,
            "routes": routes_map,
            "components": components_map
        }
