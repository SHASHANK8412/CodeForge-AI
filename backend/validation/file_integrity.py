"""
AIForge Autonomous Engineering Platform — FileIntegrityLayer
==============================================================
Centralized file representation and completeness validation:
- Standardized FileRepresentation (path, content, language, size, sha256, generated_by)
- Language- and functionality-aware content integrity checks
- Rejection of null, empty, whitespace-only, comment-only, or truncated files
"""

import hashlib
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.validation.integrity")


class FileRepresentation(BaseModel):
    path: str
    content: str
    language: str = "javascript"
    size: int = 0
    lines: int = 0
    sha256: str = ""
    generated_by: str = "Agent"
    is_valid: bool = True
    status: str = "VALID"  # "VALID", "INCOMPLETE", "PLACEHOLDER", "EMPTY"
    error_message: str = ""

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.content is not None:
            raw_bytes = self.content.encode("utf-8")
            self.size = len(raw_bytes)
            self.lines = len(self.content.split("\n"))
            self.sha256 = hashlib.sha256(raw_bytes).hexdigest()


class FileIntegrityValidator:
    """
    Validates file content integrity across programming languages and functionality scopes.
    """

    ALLOWED_EMPTY_FILES = {
        "__init__.py", ".gitkeep", ".env.example", ".gitignore", "py.typed"
    }

    def validate_file_representation(
        self,
        path: str,
        content: str,
        generated_by: str = "Agent"
    ) -> FileRepresentation:
        clean_path = path.replace("\\", "/").lstrip("/")
        base_name = clean_path.split("/")[-1]

        ext = base_name.split(".")[-1].lower() if "." in base_name else ""
        lang = "javascript"
        if ext in ["py"]: lang = "python"
        elif ext in ["sql"]: lang = "sql"
        elif ext in ["json"]: lang = "json"
        elif ext in ["jsx", "tsx", "ts", "js"]: lang = "javascript"
        elif ext in ["md"]: lang = "markdown"
        elif ext in ["html"]: lang = "html"
        elif ext in ["css"]: lang = "css"
        elif ext in ["yml", "yaml"]: lang = "yaml"
        elif base_name.lower() == "dockerfile": lang = "dockerfile"

        # Check 1: Null or Empty
        if content is None or not content.strip():
            if base_name in self.ALLOWED_EMPTY_FILES:
                return FileRepresentation(
                    path=clean_path,
                    content=content or "",
                    language=lang,
                    generated_by=generated_by,
                    is_valid=True,
                    status="VALID"
                )
            return FileRepresentation(
                path=clean_path,
                content=content or "",
                language=lang,
                generated_by=generated_by,
                is_valid=False,
                status="EMPTY",
                error_message="File content is null or empty."
            )

        lines = [l.strip() for l in content.split("\n") if l.strip()]

        # Check 2: Pure comment or placeholder file
        from backend.validation.placeholder_detector import global_placeholder_detector
        placeholder_res = global_placeholder_detector.detect(clean_path, content)
        if placeholder_res.is_placeholder:
            return FileRepresentation(
                path=clean_path,
                content=content,
                language=lang,
                generated_by=generated_by,
                is_valid=False,
                status="PLACEHOLDER",
                error_message=f"Placeholder file detected: {placeholder_res.reason}"
            )

        # Check 3: Suspiciously short functional implementation
        if lang in ["python", "javascript", "sql"] and base_name not in self.ALLOWED_EMPTY_FILES:
            if len(lines) < 2 and len(content) < 40 and not any(k in content for k in ["def ", "class ", "import ", "export ", "CREATE "]):
                return FileRepresentation(
                    path=clean_path,
                    content=content,
                    language=lang,
                    generated_by=generated_by,
                    is_valid=False,
                    status="INCOMPLETE",
                    error_message=f"File is suspiciously short ({len(lines)} line(s), {len(content)} bytes) for an implementation file."
                )

        return FileRepresentation(
            path=clean_path,
            content=content,
            language=lang,
            generated_by=generated_by,
            is_valid=True,
            status="VALID"
        )


global_file_integrity_validator = FileIntegrityValidator()
