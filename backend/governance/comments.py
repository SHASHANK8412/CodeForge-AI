"""
AIForge Review Comments Manager
===============================
Manages code and architecture review comments, task discussions, and resolution tracking.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.governance.comments")


class ReviewCommentsManager:
    """
    Manages inline comments, task feedback, and discussion threads.
    """

    def __init__(self) -> None:
        self.comments: List[Dict[str, Any]] = [
            {
                "comment_id": "comment_1",
                "project_id": "proj_hospital",
                "file_path": "src/auth/jwt_handler.py",
                "line_number": 15,
                "author": "Security Reviewer",
                "author_role": "Reviewer",
                "comment_type": "Security Feedback",
                "text": "Ensure JWT expiration token is set to max 15 minutes with refresh token rotation.",
                "status": "open",
                "timestamp": time.time() - 3600
            }
        ]

    def add_comment(
        self,
        project_id: str,
        author: str,
        author_role: str,
        text: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        comment_type: str = "General Feedback"
    ) -> Dict[str, Any]:
        comment_id = f"comment_{int(time.time() * 1000)}"
        comment = {
            "comment_id": comment_id,
            "project_id": project_id,
            "file_path": file_path,
            "line_number": line_number,
            "author": author,
            "author_role": author_role,
            "comment_type": comment_type,
            "text": text,
            "status": "open",
            "timestamp": time.time()
        }
        self.comments.append(comment)
        _logger.info(f"ReviewCommentsManager: Added comment '{comment_id}' on project '{project_id}'")
        return comment

    def resolve_comment(self, comment_id: str, resolver: str = "Developer") -> Dict[str, Any]:
        for c in self.comments:
            if c["comment_id"] == comment_id:
                c["status"] = "resolved"
                c["resolved_by"] = resolver
                c["resolved_at"] = time.time()
                return c
        raise ValueError(f"Comment ID '{comment_id}' not found.")

    def get_comments(self, project_id: Optional[str] = None, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        res = self.comments
        if project_id:
            res = [c for c in res if c["project_id"] == project_id]
        if file_path:
            res = [c for c in res if c.get("file_path") == file_path]
        return res


global_review_comments = ReviewCommentsManager()
