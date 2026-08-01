"""
AIForge Language Server Protocol (LSP) Engine
============================================
Provides symbol-aware navigation, definition lookup, reference tracing, and diagnostic error reports across codebase files.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.analysis.ast_analyzer import global_ast_analyzer

_logger = logging.getLogger("aiforge.analysis.lsp_engine")


class LSPEngine:
    """
    Symbol-aware Language Server Protocol diagnostics and navigation engine.
    """

    def __init__(self):
        self._symbol_table: Dict[str, Dict[str, Any]] = {}

    def index_codebase(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Indexes all Python files in the codebase, building a global symbol table.
        """
        self._symbol_table.clear()
        diagnostics = []

        for path, content in files.items():
            if path.endswith(".py"):
                analysis = global_ast_analyzer.analyze_python_code(path, content)
                if not analysis["valid_syntax"]:
                    for err in analysis["syntax_errors"]:
                        diagnostics.append({
                            "file": path,
                            "severity": "ERROR",
                            "message": f"SyntaxError at line {err['line']}: {err['msg']}"
                        })

                for cls in analysis["classes"]:
                    symbol_key = f"{cls['name']}"
                    self._symbol_table[symbol_key] = {
                        "kind": "class",
                        "name": cls["name"],
                        "file": path,
                        "line": cls["line"],
                        "docstring": cls["docstring"]
                    }

                for func in analysis["functions"]:
                    symbol_key = f"{func['name']}"
                    self._symbol_table[symbol_key] = {
                        "kind": "function",
                        "name": func["name"],
                        "file": path,
                        "line": func["line"],
                        "is_async": func["is_async"],
                        "docstring": func["docstring"]
                    }

        _logger.info(f"LSPEngine: Indexed {len(self._symbol_table)} global symbols across codebase")
        return {
            "symbol_count": len(self._symbol_table),
            "diagnostics": diagnostics,
            "symbols": self._symbol_table
        }

    def find_definition(self, symbol_name: str) -> Optional[Dict[str, Any]]:
        """
        Finds definition location for a symbol name.
        """
        return self._symbol_table.get(symbol_name)


global_lsp_engine = LSPEngine()
