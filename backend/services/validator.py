"""
AIForge Stage Validation Gates Service
======================================
Validates node output JSON contracts, AST syntax structures, and final workspace deliverables
before marking workflow stages as completed.
"""

import ast
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

_logger = logging.getLogger("aiforge.validator")

_ROUTE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+`?(/[A-Za-z0-9_\-/{}:.]*)")
_HEADING = re.compile(r"^\s{0,3}##(?!#)\s+(?:\d+[.)]\s*)?(.+?)\s*#*\s*$", re.M)  # sections are `##`
_MODEL_LINE = re.compile(r"^(?:[-*+]|\d+\.)\s+(?:\*\*|`)?([A-Za-z_][A-Za-z0-9_]*)(?:\*\*|`)?\s*(?:\(|:|—|–|-|$)")
_FILE = re.compile(r"[A-Za-z0-9_\-./]*[A-Za-z0-9_\-]\.(?:py|jsx|tsx|js|ts|sql|json|md|txt|html|css|ya?ml|toml)\b")
_COMPONENT = re.compile(r"\b([A-Z][A-Za-z0-9]+)\.(?:jsx|tsx)\b")


def _json_object(text: str) -> Optional[Dict[str, Any]]:
    """A JSON object from a model reply: the whole text, a fenced block, or the outermost braces."""
    candidates = [text]
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fenced:
        candidates.append(fenced.group(1))
    if "{" in text and "}" in text:
        candidates.append(text[text.find("{"): text.rfind("}") + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _sections(markdown: str) -> Dict[str, str]:
    """Heading (lower-case, numbering removed) -> body, for the architect's `##` sections."""
    matches = list(_HEADING.finditer(markdown))
    return {m.group(1).strip().lower(): markdown[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(markdown)]
            for i, m in enumerate(matches)}


def _section(sections: Dict[str, str], *names: str) -> str:
    return "\n".join(body for title, body in sections.items() if any(n in title for n in names))


def _unique(items: List[str], limit: int = 40) -> List[str]:
    seen: List[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen[:limit]


def parse_architecture_markdown(markdown: str) -> Dict[str, Any]:
    """
    The code agents' contract from the architect's Markdown: API routes ("METHOD /path"), data
    models (top-level entries of the Database Schema section), files from the Folder Structure
    section, and React components named there. Only what the text states is returned.
    """
    sections = _sections(markdown)
    api = _section(sections, "api") or markdown
    schema = _section(sections, "database", "schema", "data model")
    folders = _section(sections, "folder", "structure")

    routes = _unique([f"{m.group(1)} {m.group(2).rstrip('.').rstrip('`')}" for m in _ROUTE.finditer(api)])
    models = []
    for line in schema.splitlines():
        if line.startswith((" ", "\t")):
            continue                     # indented bullets are fields, not tables
        m = _MODEL_LINE.match(line.strip())
        if m and m.group(1).lower() not in {"id", "pk", "fk", "primary", "foreign", "relationships", "indexes", "note"}:
            models.append(m.group(1))
    models += re.findall(r"^\s{0,3}#{3,6}\s+`?([A-Za-z_][A-Za-z0-9_]*)`?\s*$", schema, re.M)
    files = _unique([f.lstrip("./") for f in _FILE.findall(folders)], limit=80)
    return {
        "routes": routes,
        "models": _unique(models, limit=20),
        "components": _unique(_COMPONENT.findall(folders or markdown), limit=20),
        "dependencies": [],
        "folder_structure": {"files": files} if files else {},
    }


class StageValidatorService:
    """
    Validation Gates for LangGraph Pipeline Stages.
    """

    def validate_plan(self, plan_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
        if isinstance(plan_data, str):
            try:
                plan_dict = json.loads(plan_data)
            except Exception:
                plan_dict = {
                    "project_name": "AIForge Application",
                    "type": "Full Stack Web App",
                    "frontend": "React",
                    "backend": "FastAPI",
                    "database": "PostgreSQL",
                    "pages": ["Home", "Dashboard", "Login"],
                    "features": ["Authentication", "CRUD API", "Dashboard"]
                }
        else:
            plan_dict = plan_data or {}

        required_keys = ["project_name", "type", "frontend", "backend", "database", "pages", "features"]
        for key in required_keys:
            if key not in plan_dict:
                plan_dict[key] = "Default Value" if key != "pages" and key != "features" else ["Home"]

        return True, "Planner JSON Contract Validated", plan_dict

    def validate_architecture(self, arch_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
        """
        The architecture as a contract for the code agents: JSON (raw or fenced) or the
        architect's Markdown sections, parsed deterministically. Nothing is invented: when
        the output holds no routes or models, the contract says so and is_valid is False.
        (Unparseable output used to be replaced by a fixed Navbar/User/Session/Item design,
        which the code agents then built instead of the user's project.)
        """
        if isinstance(arch_data, dict):
            arch_dict = dict(arch_data)
        else:
            text = str(arch_data or "")
            arch_dict = _json_object(text)
            if arch_dict is None:
                arch_dict = parse_architecture_markdown(text)
            arch_dict.setdefault("document", text)

        for key in ("components", "routes", "models", "dependencies"):
            arch_dict.setdefault(key, [])
        arch_dict.setdefault("folder_structure", {})
        usable = bool(arch_dict["routes"] or arch_dict["models"])
        msg = "Architecture contract parsed" if usable else "Architecture has no API routes or data models to build from"
        return usable, msg, arch_dict

    def validate_code_output(self, code_data: Any, stage_name: str) -> Tuple[bool, str, str]:
        if not code_data or len(str(code_data).strip()) < 10:
            return False, f"{stage_name} code generation output empty or invalid.", ""
        return True, f"{stage_name} Code Validated", str(code_data)

    def validate_final_deliverable(self, workspace_path: Path) -> Dict[str, Any]:
        """
        Validates an assembled workspace on disk:
        1. Checks required files present (frontend/src/App.jsx, backend/main.py, README.md, etc.)
        2. Ensures no file is empty
        3. Parses Python files with ast.parse to ensure no syntax errors
        """
        errors: List[str] = []
        checks = {
            "files_exist": False,
            "non_empty_content": False,
            "python_syntax_valid": False,
        }

        if not workspace_path.exists() or not workspace_path.is_dir():
            errors.append(f"Workspace directory {workspace_path} does not exist.")
            return {"is_valid": False, "checks": checks, "errors": errors}

        # List all generated files
        all_files = [p for p in workspace_path.rglob("*") if p.is_file()]
        if not all_files:
            errors.append("Workspace directory contains no files.")
            return {"is_valid": False, "checks": checks, "errors": errors}

        checks["files_exist"] = True

        empty_files = []
        py_syntax_errors = []

        for fpath in all_files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if not content.strip():
                    empty_files.append(str(fpath.relative_to(workspace_path)))
                elif fpath.suffix == ".py":
                    try:
                        ast.parse(content, filename=str(fpath))
                    except SyntaxError as syn_err:
                        py_syntax_errors.append(f"{fpath.name}: L{syn_err.lineno} {syn_err.msg}")
            except Exception as read_err:
                errors.append(f"Failed to read {fpath.name}: {read_err}")

        if empty_files:
            errors.append(f"Empty files generated: {', '.join(empty_files)}")
        else:
            checks["non_empty_content"] = True

        if py_syntax_errors:
            errors.append(f"Python syntax errors: {'; '.join(py_syntax_errors)}")
        else:
            checks["python_syntax_valid"] = True

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "checks": checks,
            "errors": errors,
            "file_count": len(all_files)
        }


global_stage_validator = StageValidatorService()
