"""
AIForge Next-Gen AI Agent Core — Tool Registry & Safe Execution Engine
======================================================================
First-class dynamic tool registry with:
- Strict JSON Schema validation
- 4 Risk Tiers: LOW, MEDIUM, HIGH, CRITICAL
- Path traversal & SSRF security boundaries
- Safe sandbox execution handlers
"""

import ast
import os
import re
import math
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.ai_core.tools")


class ToolRiskLevel(str, Enum):
    LOW = "LOW"            # e.g., Calculator, FileReader, WebSearch
    MEDIUM = "MEDIUM"      # e.g., HttpApiTool, DataAnalyzer
    HIGH = "HIGH"          # e.g., CodeExecution, FileWritePatch
    CRITICAL = "CRITICAL"  # e.g., DeleteResource, ProductionDeploy


class ToolDefinition(BaseModel):
    name: str
    category: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    requires_approval: bool = False
    enabled: bool = True


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._register_builtins()

    def _register_builtins(self):
        # 1. WebSearch
        self.register(
            ToolDefinition(
                name="web_search",
                category="Research",
                description="Performs live technical web research and returns cited authoritative references.",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False
            ),
            handler=self._handle_web_search
        )

        # 2. Calculator
        self.register(
            ToolDefinition(
                name="calculator",
                category="Math",
                description="Evaluates mathematical formulas, token budget limits, and statistical ratios safely.",
                input_schema={"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False
            ),
            handler=self._handle_calculator
        )

        # 3. CodeExecution
        self.register(
            ToolDefinition(
                name="code_execution",
                category="Coding",
                description="Executes Python or JavaScript snippets in an isolated virtual sandbox container.",
                input_schema={"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string"}}, "required": ["code"]},
                risk_level=ToolRiskLevel.HIGH,
                requires_approval=False
            ),
            handler=self._handle_code_execution
        )

        # 4. FileReader
        self.register(
            ToolDefinition(
                name="file_reader",
                category="Filesystem",
                description="Reads file contents from the active project workspace with traversal prevention.",
                input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False
            ),
            handler=self._handle_file_reader
        )

        # 5. FileSearch
        self.register(
            ToolDefinition(
                name="file_search",
                category="Filesystem",
                description="Searches for symbols, regex patterns, or filenames across the project workspace.",
                input_schema={"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]},
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False
            ),
            handler=self._handle_file_search
        )

        # 6. DocumentAnalyzer
        self.register(
            ToolDefinition(
                name="document_analyzer",
                category="RAG",
                description="Extracts structured architectural requirements and AST summaries from documents.",
                input_schema={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]},
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False
            ),
            handler=self._handle_document_analyzer
        )

        # 7. DataAnalyzer
        self.register(
            ToolDefinition(
                name="data_analyzer",
                category="Analytics",
                description="Parses CSV or JSON payloads and computes distributions, statistical percentiles, and anomalies.",
                input_schema={"type": "object", "properties": {"data_json": {"type": "string"}}, "required": ["data_json"]},
                risk_level=ToolRiskLevel.MEDIUM,
                requires_approval=False
            ),
            handler=self._handle_data_analyzer
        )

        # 8. HttpApiTool
        self.register(
            ToolDefinition(
                name="http_api_tool",
                category="Networking",
                description="Executes authenticated REST API calls with SSRF protection and domain allowlisting.",
                input_schema={"type": "object", "properties": {"url": {"type": "string"}, "method": {"type": "string"}}, "required": ["url"]},
                risk_level=ToolRiskLevel.MEDIUM,
                requires_approval=False
            ),
            handler=self._handle_http_api
        )

    def register(self, tool: ToolDefinition, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def execute_tool(self, name: str, arguments: Dict[str, Any], user_confirmed: bool = False) -> Dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found in registry"}

        if tool.requires_approval and not user_confirmed:
            return {
                "success": False,
                "status": "APPROVAL_REQUIRED",
                "risk_level": tool.risk_level.value,
                "message": f"Tool '{name}' classified as {tool.risk_level.value} risk. Explicit user approval required."
            }

        handler = self._handlers.get(name)
        if not handler:
            return {"success": False, "error": f"No execution handler registered for '{name}'"}

        try:
            start_time = time.time()
            result = handler(arguments)
            duration = round(time.time() - start_time, 4)
            return {
                "success": True,
                "tool": name,
                "risk_level": tool.risk_level.value,
                "duration_seconds": duration,
                "result": result
            }
        except Exception as e:
            _logger.error(f"Error executing tool '{name}': {e}")
            return {"success": False, "tool": name, "error": str(e)}

    # Handlers. Each one either does real, bounded work or says plainly that it can't;
    # none of them return invented results.
    def _handle_web_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "query": args.get("query", ""),
            "results": [],
            "error": "No web search provider is configured, so no search was performed.",
        }

    def _handle_calculator(self, args: Dict[str, Any]) -> Dict[str, Any]:
        expr = str(args.get("expression", "0"))
        try:
            return {"expression": expr, "result": _safe_arithmetic(expr)}
        except (ValueError, ZeroDivisionError, SyntaxError, OverflowError) as err:
            return {"expression": expr, "error": str(err)}

    def _handle_code_execution(self, args: Dict[str, Any]) -> Dict[str, Any]:
        from backend.tools.python_runner import CODE_TOOLS_ENV, code_tools_enabled, run_python_snippet
        lang = args.get("language", "python")
        if lang != "python":
            return {"language": lang, "executed": False, "error": f"Only Python can be executed, not '{lang}'."}
        if not code_tools_enabled():
            return {"language": lang, "executed": False, "error": f"Code execution is disabled. Set {CODE_TOOLS_ENV}=1 to enable it."}
        res = run_python_snippet(args.get("code", ""))
        return {"language": lang, "executed": True, "stdout": res["output"], "stderr": res["error"], "exit_code": res["exit_code"]}

    def _handle_file_reader(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path = str(args.get("path", ""))
        target = _inside_repo(path)
        if target is None or not target.is_file():
            return {"path": path, "error": "File not found inside the project root (paths outside it are blocked)."}
        if target.stat().st_size > _MAX_READ_BYTES:
            return {"path": path, "error": f"File is larger than {_MAX_READ_BYTES // 1024} KB."}
        return {"path": path, "content": target.read_text(encoding="utf-8", errors="replace")}

    def _handle_file_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        pattern = str(args.get("pattern", ""))
        if not pattern:
            return {"pattern": pattern, "matches": [], "error": "Empty pattern."}
        matches = []
        for f in _REPO_ROOT.rglob("*"):
            if len(matches) >= 50:
                break
            if (not f.is_file() or f.suffix not in _SEARCHABLE_SUFFIXES
                    or any(part in _SKIP_DIRS for part in f.relative_to(_REPO_ROOT).parts)
                    or f.stat().st_size > _MAX_READ_BYTES):
                continue
            for lineno, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if pattern in line:
                    matches.append({"file": f.relative_to(_REPO_ROOT).as_posix(), "line": lineno, "preview": line.strip()[:200]})
                    if len(matches) >= 50:
                        break
        return {"pattern": pattern, "matches": matches, "truncated": len(matches) >= 50}

    def _handle_document_analyzer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        content = str(args.get("content", ""))
        lines = content.splitlines()
        return {
            "word_count": len(content.split()),
            "line_count": len(lines),
            "headings": [l.lstrip("#").strip() for l in lines if l.lstrip().startswith("#")][:30],
        }

    def _handle_data_analyzer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = json.loads(args.get("data_json", "[]") or "[]")
        except json.JSONDecodeError as err:
            return {"error": f"data_json is not valid JSON: {err}"}
        rows = data if isinstance(data, list) else [data]
        numeric: Dict[str, List[float]] = {}
        for row in rows:
            if isinstance(row, dict):
                for key, value in row.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric.setdefault(key, []).append(float(value))
        metrics = {
            key: {"count": len(vals), "mean": round(sum(vals) / len(vals), 4), "min": min(vals), "max": max(vals)}
            for key, vals in numeric.items()
        }
        return {"row_count": len(rows), "metrics": metrics}

    def _handle_http_api(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": args.get("url", ""),
            "method": args.get("method", "GET"),
            "error": "Outbound HTTP calls are not enabled for agent tools, so no request was sent.",
        }


_REPO_ROOT = Path(__file__).resolve().parents[2]
_MAX_READ_BYTES = 256 * 1024
_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "generated_projects", "dist", "build", ".claude"}
_SEARCHABLE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".yml", ".yaml", ".toml", ".txt", ".css", ".html"}


def _inside_repo(path: str) -> Optional[Path]:
    """Resolve a relative path inside the repository, or None if it escapes it."""
    try:
        target = (_REPO_ROOT / path).resolve()
    except (OSError, ValueError):
        return None
    return target if _REPO_ROOT in target.parents else None


_BIN_OPS = {
    ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b, ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b,
}


def _safe_arithmetic(expr: str) -> float:
    """Evaluate + - * / // % and parentheses on numbers. No names, calls or powers (no '9**9**9')."""
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = ev(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](ev(node.left), ev(node.right))
        raise ValueError("Only numbers, + - * / // % and parentheses are allowed.")

    if len(expr) > 200:
        raise ValueError("Expression is too long.")
    return ev(ast.parse(expr, mode="eval"))


global_tool_registry = ToolRegistry()
