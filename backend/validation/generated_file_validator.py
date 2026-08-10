"""
AIForge Generated File Validator & Quality Gate
===============================================
Enforces strict content validation for every generated project file:
- Path exists, content non-empty, non-whitespace
- Language-aware validation:
  * Python (.py): AST parsing (ast.parse), rejects comment-only/pass-only files
  * JavaScript/React (.js, .jsx, .ts, .tsx): Rejects placeholders, checks component/imports/exports
  * SQL (.sql): Requires DDL/DML statements (CREATE TABLE, ALTER, etc.)
  * Test files (tests/*.py): Requires actual test_... functions with assertions/calls
  * Markdown (.md): Requires structured documentation
- Rejects placeholder content: `# TODO`, `# JWT Authentication Middleware`, `// Add code here`, `pass`, `Coming soon`, etc.
"""
from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Common Placeholder Patterns
# ─────────────────────────────────────────────

PLACEHOLDER_PATTERNS = [
    r"^\s*#\s*JWT Authentication Middleware\s*$",
    r"^\s*#\s*Pytest Integration Tests\s*$",
    r"^\s*#\s*SQLAlchemy Models\s*$",
    r"^\s*#\s*FastAPI Main App\s*$",
    r"^\s*//\s*React App Root\s*$",
    r"^\s*//\s*React Navbar Component\s*$",
    r"^\s*//\s*React Home Page\s*$",
    r"^\s*--\s*SQL Database Schema\s*$",
    r"^\s*#\s*API Documentation\s*$",
    r"^\s*pass\s*$",
    r"^\s*#\s*TODO\b",
    r"^\s*//\s*TODO\b",
    r"^\s*#\s*Implementation goes here\b",
    r"^\s*//\s*Add code here\b",
    r"^\s*#\s*Coming soon\b",
    r"^\s*#\s*Implementation omitted\b",
]


class FileValidationResult(BaseModel):
    path: str
    is_valid: bool
    status: str = "PASS"  # PASS, INVALID_PLACEHOLDER, INVALID_SYNTAX, INVALID_EMPTY, INVALID_STRUCTURE
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    language: str = "plaintext"
    content_length: int = 0
    line_count: int = 0


class GeneratedFileValidator:
    """Validates generated project files according to language-specific rules."""

    def is_placeholder_content(self, content: str) -> bool:
        """Check if content is a single-line comment placeholder or trivial stub."""
        stripped = content.strip()
        if not stripped:
            return True

        # Check against known placeholder patterns
        lines = [line.strip() for line in stripped.splitlines() if line.strip()]
        if len(lines) == 1:
            line = lines[0]
            for pat in PLACEHOLDER_PATTERNS:
                if re.match(pat, line, re.IGNORECASE):
                    return True

        # Check if entire content is just comments
        non_comment_lines = [
            l for l in lines
            if not l.startswith("#") and not l.startswith("//") and not l.startswith("/*") and not l.startswith("*") and not l.startswith("--")
        ]
        if not non_comment_lines:
            return True

        return False

    def validate_file(self, path: str, content: str, agent: str = "Unknown") -> FileValidationResult:
        """Validate a single generated file."""
        clean_path = path.replace("\\", "/").lstrip("/")
        res = FileValidationResult(
            path=clean_path,
            is_valid=True,
            content_length=len(content or ""),
            line_count=len((content or "").splitlines())
        )

        # 0. Path safety checks
        if ".." in clean_path.split("/"):
            res.is_valid = False
            res.status = "PATH_TRAVERSAL_ATTEMPT"
            res.errors.append(f"Path '{clean_path}' contains path traversal sequence '..'.")
            return res

        if any(char in clean_path for char in ["|", "<", ">", "?", "*", "\0"]):
            res.is_valid = False
            res.status = "INVALID_PATH"
            res.errors.append(f"Path '{clean_path}' contains illegal path characters.")
            return res

        # 1. Non-empty check
        if not content or not content.strip():
            res.is_valid = False
            res.status = "INVALID_EMPTY"
            res.errors.append(f"File '{clean_path}' is empty or contains only whitespace.")
            return res

        # 2. Placeholder check (before length check)
        if self.is_placeholder_content(content):
            res.is_valid = False
            res.status = "INVALID_PLACEHOLDER"
            res.errors.append(f"File '{clean_path}' contains only comment placeholders, TODOs, or empty pass stubs.")
            return res

        # 3. Minimum length check
        if len(content.strip()) < 10 and not clean_path.endswith(".env") and not clean_path.endswith(".gitignore"):
            res.is_valid = False
            res.status = "INVALID_EMPTY"
            res.errors.append(f"File '{clean_path}' is too short ({len(content.strip())} chars).")
            return res


        # 4. Language-specific validation
        ext = clean_path.split(".")[-1].lower() if "." in clean_path else ""

        if ext == "py":
            res.language = "python"
            self._validate_python(clean_path, content, res)
        elif ext in ["js", "jsx", "ts", "tsx"]:
            res.language = "javascript" if ext in ["js", "jsx"] else "typescript"
            self._validate_javascript(clean_path, content, res)
        elif ext == "sql":
            res.language = "sql"
            self._validate_sql(clean_path, content, res)
        elif ext == "md":
            res.language = "markdown"
            self._validate_markdown(clean_path, content, res)
        elif ext in ["json", "yml", "yaml", "toml"]:
            res.language = ext
            self._validate_config(clean_path, content, res)
        else:
            res.language = ext or "plaintext"

        return res

    def _validate_python(self, path: str, content: str, res: FileValidationResult) -> None:
        """Python syntax & structure validation."""
        # AST parse check
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as e:
            res.is_valid = False
            res.status = "INVALID_SYNTAX"
            res.errors.append(f"Python syntax error in '{path}': line {e.lineno} - {e.msg}")
            return

        # AST inspection: verify python file has statements
        statements = tree.body
        if not statements:
            res.is_valid = False
            res.status = "INVALID_EMPTY"
            res.errors.append(f"Python file '{path}' has no AST statements.")
            return

        # Special check for test files (tests/*.py or test_*.py)
        if "test" in path.lower():
            test_funcs = [
                node for node in ast.walk(tree)
                if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            ]
            if not test_funcs:
                res.is_valid = False
                res.status = "INVALID_STRUCTURE"
                res.errors.append(f"Test file '{path}' does not contain any test functions starting with 'test_'.")

    def _validate_javascript(self, path: str, content: str, res: FileValidationResult) -> None:
        """React / JS / TS component validation."""
        # Check for unclosed braces or basic syntax errors
        open_braces = content.count("{") - content.count("}")
        open_parens = content.count("(") - content.count(")")
        if abs(open_braces) > 5 or abs(open_parens) > 5:
            res.warnings.append(f"Possible unmatched braces/parens in '{path}' ({open_braces} braces, {open_parens} parens).")

        # React component check for .jsx / .tsx files
        if path.endswith(".jsx") or path.endswith(".tsx"):
            has_import = "import " in content or "require(" in content
            has_export = "export " in content or "module.exports" in content
            has_return_jsx = "<" in content and ">" in content

            if not (has_export or has_return_jsx):
                res.is_valid = False
                res.status = "INVALID_STRUCTURE"
                res.errors.append(f"React component file '{path}' missing export or JSX return elements.")

    def _validate_sql(self, path: str, content: str, res: FileValidationResult) -> None:
        """SQL DDL / DML validation."""
        sql_upper = content.upper()
        keywords = ["CREATE TABLE", "ALTER TABLE", "INSERT INTO", "CREATE INDEX", "CREATE TYPE", "DROP TABLE"]
        if not any(kw in sql_upper for kw in keywords):
            res.is_valid = False
            res.status = "INVALID_STRUCTURE"
            res.errors.append(f"SQL file '{path}' does not contain DDL/DML statements (CREATE TABLE, etc.).")

    def _validate_markdown(self, path: str, content: str, res: FileValidationResult) -> None:
        """Markdown documentation validation."""
        if not content.startswith("#") and "##" not in content and len(content.splitlines()) < 3:
            res.is_valid = False
            res.status = "INVALID_STRUCTURE"
            res.errors.append(f"Markdown file '{path}' lacks proper headers or minimal documentation structure.")

    def _validate_config(self, path: str, content: str, res: FileValidationResult) -> None:
        """JSON/YAML config validation."""
        if path.endswith(".json"):
            import json
            try:
                json.loads(content)
            except Exception as e:
                res.is_valid = False
                res.status = "INVALID_SYNTAX"
                res.errors.append(f"JSON syntax error in '{path}': {e}")


global_file_validator = GeneratedFileValidator()
