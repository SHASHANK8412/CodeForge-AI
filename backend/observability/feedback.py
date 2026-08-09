import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "data" / "feedback.json"
FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

FEEDBACK_STORE: List[dict] = []


def _load_feedback():
    if FEEDBACK_STORE:
        return
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                FEEDBACK_STORE.extend(data)
        except Exception:
            pass


def _save_feedback():
    try:
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(FEEDBACK_STORE, f, indent=2)
    except Exception:
        pass


_load_feedback()


class FeedbackSubmissionRequest(BaseModel):
    project_id: str
    helpful: bool = True
    rating: int = Field(default=5, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    comment: Optional[str] = ""


def submit_user_feedback(user_id: str, req: FeedbackSubmissionRequest) -> dict:
    _load_feedback()
    entry = {
        "id": f"fb_{len(FEEDBACK_STORE) + 1}",
        "user_id": user_id,
        "project_id": req.project_id,
        "helpful": req.helpful,
        "rating": req.rating,
        "tags": req.tags,
        "comment": req.comment,
        "created_at": datetime.now().isoformat()
    }
    FEEDBACK_STORE.append(entry)
    _save_feedback()
    return entry


def get_project_feedback(project_id: str) -> List[dict]:
    _load_feedback()
    return [fb for fb in FEEDBACK_STORE if fb["project_id"] == project_id]
