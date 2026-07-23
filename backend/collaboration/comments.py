"""
AIForge Context-Aware Comments & Discussion Engine
===================================================
Links developer & AI discussion comments directly to specific files, lines of code, and tasks.
"""

import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.collaboration")


class CommentEngine:
    """
    Manages code line comments and file-linked discussion threads.
    """

    def __init__(self) -> None:
        self.comments: List[Dict[str, Any]] = []

    def add_comment(
        self,
        user_id: str,
        user_name: str,
        file_path: str,
        comment_text: str,
        line_number: int = 1
    ) -> Dict[str, Any]:
        comment = {
            "comment_id": f"cmt_{len(self.comments) + 1}",
            "user_id": user_id,
            "user_name": user_name,
            "file_path": file_path,
            "line_number": line_number,
            "comment_text": comment_text,
            "timestamp": time.time()
        }
        self.comments.append(comment)
        _logger.info(f"CommentEngine: Added comment on {file_path}:{line_number} by {user_name}")
        return comment

    def get_comments_for_file(self, file_path: str) -> List[Dict[str, Any]]:
        return [c for c in self.comments if c.get("file_path") == file_path]


global_comment_engine = CommentEngine()
