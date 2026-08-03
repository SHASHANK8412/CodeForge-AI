"""
AIForge Symbol Extractor
========================
Extracts deterministic code symbols (functions, classes, methods, imports, routes, models)
using Python AST parser and structured pattern matchers.
"""

import ast
import re
import logging
from typing import List, Tuple, Dict, Any
from backend.repository.models import SymbolRecord

_logger = logging.getLogger("aiforge.repository.symbols")


class SymbolExtractor:
    """
    Extracts structured symbols from Python, JavaScript/TypeScript, and Java code files.
    """

    def extract_symbols(self, file_path: str, content: str, language: str) -> Tuple[List[SymbolRecord], List[str]]:
        symbols: List[SymbolRecord] = []
        imports: List[str] = []

        if not content:
            return symbols, imports

        lang = language.lower()

        if lang == "python":
            symbols, imports = self._extract_python_ast(file_path, content)
        elif lang in ["javascript", "typescript", "js", "ts", "jsx", "tsx"]:
            symbols, imports = self._extract_js_symbols(file_path, content)
        elif lang == "java":
            symbols, imports = self._extract_java_symbols(file_path, content)

        return symbols, imports

    def _extract_python_ast(self, file_path: str, content: str) -> Tuple[List[SymbolRecord], List[str]]:
        symbols: List[SymbolRecord] = []
        imports: List[str] = []

        try:
            tree = ast.parse(content)
        except Exception as e:
            _logger.debug(f"[SymbolExtractor] Python AST parse fallback for '{file_path}': {e}")
            return symbols, imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

            elif isinstance(node, ast.ClassDef):
                sym = SymbolRecord(
                    name=node.name,
                    kind="model" if any("Base" in str(b) or "Model" in str(b) for b in node.bases) else "class",
                    file=file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    signature=f"class {node.name}"
                )
                symbols.append(sym)

            elif isinstance(node, ast.FunctionDef) or isinstance(node, (ast.AsyncFunctionDef if hasattr(ast, "AsyncFunctionDef") else ast.FunctionDef)):
                # Detect FastAPI route decorators
                is_route = False
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in ["get", "post", "put", "delete", "patch"]:
                            is_route = True
                            break

                sym = SymbolRecord(
                    name=node.name,
                    kind="route" if is_route else "function",
                    file=file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    signature=f"def {node.name}(...)"
                )
                symbols.append(sym)

        return symbols, imports

    def _extract_js_symbols(self, file_path: str, content: str) -> Tuple[List[SymbolRecord], List[str]]:
        symbols: List[SymbolRecord] = []
        imports: List[str] = []

        # Extract import statements
        import_matches = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", content)
        imports.extend(import_matches)

        # Extract function definitions
        fn_matches = re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\((.*?)\)", content)
        for m in fn_matches:
            line_no = content[:m.start()].count("\n") + 1
            symbols.append(
                SymbolRecord(
                    name=m.group(1),
                    kind="function",
                    file=file_path,
                    line_start=line_no,
                    line_end=line_no + 10,
                    signature=f"function {m.group(1)}({m.group(2)})"
                )
            )

        # Extract Class definitions
        cls_matches = re.finditer(r"(?:export\s+)?class\s+([A-Za-z0-9_]+)", content)
        for m in cls_matches:
            line_no = content[:m.start()].count("\n") + 1
            symbols.append(
                SymbolRecord(
                    name=m.group(1),
                    kind="class",
                    file=file_path,
                    line_start=line_no,
                    line_end=line_no + 20,
                    signature=f"class {m.group(1)}"
                )
            )

        return symbols, imports

    def _extract_java_symbols(self, file_path: str, content: str) -> Tuple[List[SymbolRecord], List[str]]:
        symbols: List[SymbolRecord] = []
        imports: List[str] = []

        import_matches = re.findall(r"import\s+([A-Za-z0-9_\.]+);", content)
        imports.extend(import_matches)

        cls_matches = re.finditer(r"(?:public|protected|private)?\s*class\s+([A-Za-z0-9_]+)", content)
        for m in cls_matches:
            line_no = content[:m.start()].count("\n") + 1
            symbols.append(
                SymbolRecord(
                    name=m.group(1),
                    kind="class",
                    file=file_path,
                    line_start=line_no,
                    line_end=line_no + 30,
                    signature=f"class {m.group(1)}"
                )
            )

        return symbols, imports


global_symbol_extractor = SymbolExtractor()
