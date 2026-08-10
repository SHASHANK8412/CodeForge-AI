"""
AIForge Autonomous Engineering Platform — PlaceholderDetector
===============================================================
Detects placeholder code, comment-only files, TODO stubs, and abbreviated implementations.
"""

import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.validation.placeholder")


class PlaceholderDetectionResult(BaseModel):
    is_placeholder: bool = False
    reason: str = ""
    snippet: str = ""


class PlaceholderDetector:
    """
    Contextual detector for placeholder comments, TODO stubs, and incomplete source files.
    """

    ALLOWED_SPECIAL_FILES = {
        "__init__.py", ".gitkeep", ".env.example", ".gitignore", "py.typed"
    }

    def detect(self, filepath: str, content: str) -> PlaceholderDetectionResult:
        base_name = filepath.replace("\\", "/").split("/")[-1]
        if base_name in self.ALLOWED_SPECIAL_FILES:
            return PlaceholderDetectionResult(is_placeholder=False)

        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if not lines:
            return PlaceholderDetectionResult(is_placeholder=True, reason="File is empty", snippet="")

        full_text = content.lower()
        if len(lines) <= 5:
            for stub in ["// todo", "# todo", "/* todo", "implement here", "coming soon", "placeholder", "your code here"]:
                if stub in full_text:
                    return PlaceholderDetectionResult(
                        is_placeholder=True,
                        reason=f"File contains stub text '{stub}'",
                        snippet=lines[0][:100]
                    )

        # Pattern 2: File contains ONLY comments (e.g. "# JWT Authentication Middleware")
        non_comment_lines = [
            l for l in lines
            if not l.startswith(("#", "//", "/*", "*", "--", "<!--")) and l not in ["pass", "...", "{", "}"]
        ]

        if not non_comment_lines and len(lines) <= 5:
            return PlaceholderDetectionResult(
                is_placeholder=True,
                reason="File contains only comment lines or trivial pass/ellipsis statements",
                snippet=lines[0][:100]
            )

        # Pattern 3: Python pass-only or ellipsis-only function stubs
        if len(lines) <= 2 and any(l in ["pass", "...", "return None"] for l in lines):
            if not any(k in content for k in ["import ", "from ", "class ", "export "]):
                return PlaceholderDetectionResult(
                    is_placeholder=True,
                    reason="Single pass/ellipsis statement without implementation code",
                    snippet=lines[0][:100]
                )

        return PlaceholderDetectionResult(is_placeholder=False)


global_placeholder_detector = PlaceholderDetector()
