"""
AIForge Live AI Canvas Service
==============================
Backend engine for managing persistent, interactive, multi-modal live canvases:
- Canvas Types: DOCUMENT, CODE, ROADMAP, TABLE, DIAGRAM, VISUALIZATION, NOTES, MARKDOWN
- 2-Way AI Synchronization & Selection-Based AI Transforms
- Version History Snapshot Engine (Create, Compare, Restore)
- Project & AI Memory Integration
"""

import os
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path

from backend.memory.ai_memory_service import global_ai_memory_service

_logger = logging.getLogger("aiforge.canvas.service")


class CanvasType(str, Enum):
    DOCUMENT = "DOCUMENT"
    CODE = "CODE"
    ROADMAP = "ROADMAP"
    TABLE = "TABLE"
    DIAGRAM = "DIAGRAM"
    VISUALIZATION = "VISUALIZATION"
    NOTES = "NOTES"
    MARKDOWN = "MARKDOWN"


class CanvasVersion(BaseModel):
    version_id: str = Field(default_factory=lambda: f"v_{uuid.uuid4().hex[:8]}")
    version_number: int
    title: str
    content: Any  # text, markdown, or structured JSON
    canvas_type: CanvasType
    author: str = "AI"  # "User" or "AI"
    change_summary: str = "Update"
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class CanvasItem(BaseModel):
    id: str = Field(default_factory=lambda: f"canvas_{uuid.uuid4().hex[:10]}")
    title: str
    canvas_type: CanvasType = CanvasType.DOCUMENT
    content: Any
    files: Optional[Dict[str, str]] = None  # For CODE canvas: {"main.py": "...", "config.py": "..."}
    project_id: Optional[str] = None
    owner_id: Optional[str] = None  # the user who created the canvas
    tags: List[str] = Field(default_factory=list)
    versions: List[CanvasVersion] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


# Rich Starter Demo Canvases
class CanvasService:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "canvas"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "live_canvases.json"
        self._canvases: Dict[str, CanvasItem] = {}
        self._load()

    def _load(self):
        if not self.storage_file.exists():
            return
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for item_dict in json.load(f):
                    if not item_dict.get("owner_id"):
                        continue          # sample canvases from earlier versions belong to nobody
                    item = CanvasItem(**item_dict)
                    self._canvases[item.id] = item
        except Exception as e:
            _logger.error(f"Error loading canvases: {e}")

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in self._canvases.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving canvases: {e}")

    def list_canvases(self, owner_id: str, project_id: Optional[str] = None, canvas_type: Optional[str] = None) -> List[CanvasItem]:
        items = [c for c in self._canvases.values() if c.owner_id == owner_id]
        if project_id:
            items = [c for c in items if c.project_id == project_id]
        if canvas_type and canvas_type != "ALL":
            items = [c for c in items if c.canvas_type.value == canvas_type]
        items.sort(key=lambda c: c.updated_at, reverse=True)
        return items

    def get_canvas(self, canvas_id: str, owner_id: str) -> Optional[CanvasItem]:
        canvas = self._canvases.get(canvas_id)
        return canvas if canvas is not None and canvas.owner_id == owner_id else None

    def create_canvas(
        self,
        title: str,
        canvas_type: CanvasType = CanvasType.DOCUMENT,
        content: Any = None,
        files: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        owner_id: Optional[str] = None,
    ) -> CanvasItem:
        if content is None:
            if canvas_type == CanvasType.DOCUMENT:
                content = f"# {title}\n\nStart writing..."
            elif canvas_type == CanvasType.CODE:
                content = "# Python Code Workspace\nprint('Hello from AIForge Canvas!')\n"
            elif canvas_type == CanvasType.ROADMAP:
                content = [{"phase": "01", "title": "Phase 1: Foundation", "duration": "Week 1", "status": "IN_PROGRESS", "description": "Initial setup & planning.", "milestones": ["Setup", "Blueprint"]}]
            elif canvas_type == CanvasType.TABLE:
                content = {"columns": ["Item", "Category", "Status", "Notes"], "rows": [["", "", "", ""]]}
            elif canvas_type == CanvasType.DIAGRAM:
                content = [{"id": "node-1", "label": "Client", "category": "Frontend", "x": 100, "y": 100}]
            else:
                content = f"# {title}\n"

        canvas = CanvasItem(
            title=title.strip(),
            canvas_type=canvas_type,
            content=content,
            files=files or ({"main.py": content} if canvas_type == CanvasType.CODE and isinstance(content, str) else None),
            project_id=project_id,
            owner_id=owner_id,
            tags=tags or [canvas_type.value]
        )

        # Initial Version Snapshot
        canvas.versions.append(
            CanvasVersion(
                version_number=1,
                title=canvas.title,
                content=canvas.content,
                canvas_type=canvas.canvas_type,
                author="User",
                change_summary="Created Canvas"
            )
        )

        self._canvases[canvas.id] = canvas
        self._save()
        return canvas

    def update_canvas(
        self,
        canvas_id: str,
        content: Optional[Any] = None,
        title: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
        change_summary: str = "Updated Canvas",
        author: str = "User",
        canvas_type: Optional[CanvasType] = None,
    ) -> Optional[CanvasItem]:
        canvas = self._canvases.get(canvas_id)
        if not canvas:
            return None

        if title is not None:
            canvas.title = title.strip()
        if content is not None:
            canvas.content = content
        if files is not None:
            canvas.files = files
        if canvas_type is not None:
            canvas.canvas_type = canvas_type

        canvas.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Create new version snapshot if meaningful change
        next_ver = len(canvas.versions) + 1
        canvas.versions.append(
            CanvasVersion(
                version_number=next_ver,
                title=canvas.title,
                content=canvas.content,
                canvas_type=canvas.canvas_type,
                author=author,
                change_summary=change_summary
            )
        )

        self._save()
        return canvas

    def delete_canvas(self, canvas_id: str) -> bool:
        if canvas_id in self._canvases:
            del self._canvases[canvas_id]
            self._save()
            return True
        return False

    def restore_version(self, canvas_id: str, version_id: str) -> Optional[CanvasItem]:
        canvas = self._canvases.get(canvas_id)
        if not canvas:
            return None

        target_version = next((v for v in canvas.versions if v.version_id == version_id), None)
        if not target_version:
            return None

        canvas.content = target_version.content
        canvas.canvas_type = target_version.canvas_type
        canvas.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Snapshot restored action
        canvas.versions.append(
            CanvasVersion(
                version_number=len(canvas.versions) + 1,
                title=canvas.title,
                content=canvas.content,
                canvas_type=canvas.canvas_type,
                author="User",
                change_summary=f"Restored Version {target_version.version_number}"
            )
        )

        self._save()
        return canvas


global_canvas_service = CanvasService()
