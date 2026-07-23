"""
AIForge Workspace Project Model
===============================
Represents an independent software project inside the AI Engineering Organization workspace
(e.g., Ecommerce, Hospital, AIResume, CRM).
Stores source code, project memory, vector database context, logs, documentation,
chat history, tests, and deployment configs independently.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.workspace")


class WorkspaceProject:
    """
    Independent Software Project container.
    """

    def __init__(self, project_id: str, name: str, description: str = "", project_dir: Optional[str] = None) -> None:
        self.id = project_id
        self.name = name
        self.description = description
        
        if project_dir is None:
            workspace_root = Path(__file__).resolve().parents[2] / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            project_dir = str(workspace_root / name)

        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.created_at = time.time()
        self.updated_at = time.time()

        self.chat_history: List[Dict[str, Any]] = []
        self.logs: List[str] = []
        self.status = "ACTIVE"
        self._init_project_structure()

    def _init_project_structure(self) -> None:
        (self.project_dir / "src").mkdir(exist_ok=True)
        (self.project_dir / "docs").mkdir(exist_ok=True)
        (self.project_dir / "tests").mkdir(exist_ok=True)

        meta_file = self.project_dir / "project.json"
        if not meta_file.exists():
            self.save_metadata()

    def save_metadata(self) -> Dict[str, Any]:
        self.updated_at = time.time()
        meta = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chat_history_count": len(self.chat_history),
            "logs_count": len(self.logs)
        }
        try:
            with open(self.project_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save project.json for {self.name}: {e}")
        return meta

    def add_chat_message(self, role: str, content: str) -> Dict[str, Any]:
        msg = {"role": role, "content": content, "timestamp": time.time()}
        self.chat_history.append(msg)
        self.save_metadata()
        return msg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "project_dir": str(self.project_dir),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chat_history": self.chat_history,
            "logs": self.logs
        }
