"""
AIForge Error Learning & Feedback Engine
========================================
Stores software bugs, root causes, applied fixes, and prevention strategies.
When duplicate errors occur, recommends previously recorded fixes automatically.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning")


class ErrorFeedbackEngine:
    """
    Persistent error memory and automated fix recommender.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_dir = Path(__file__).resolve().parent
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "error_memory.json")
        self.db_file = Path(db_path)
        self._init_memory()

    def _init_memory(self) -> None:
        if not self.store_file_exists():
            default_errors = [
                {
                    "error_type": "ImportError",
                    "cause": "Wrong relative import path across packages",
                    "recommended_fix": "Use absolute import 'from backend.package import module'",
                    "occurrences": 2
                }
            ]
            self._save_errors(default_errors)

    def store_file_exists(self) -> bool:
        return self.db_file.exists()

    def _load_errors(self) -> List[Dict[str, Any]]:
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_errors(self, errors: List[Dict[str, Any]]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save error_memory.json: {e}")

    def record_error_and_fix(self, error_type: str, cause: str, recommended_fix: str) -> Dict[str, Any]:
        errors = self._load_errors()
        for err in errors:
            if err.get("error_type") == error_type or err.get("cause") == cause:
                err["occurrences"] = err.get("occurrences", 1) + 1
                err["recommended_fix"] = recommended_fix
                self._save_errors(errors)
                return err

        entry = {
            "error_type": error_type,
            "cause": cause,
            "recommended_fix": recommended_fix,
            "occurrences": 1
        }
        errors.append(entry)
        self._save_errors(errors)
        _logger.info(f"ErrorFeedbackEngine: Saved fix for error '{error_type}'")
        return entry

    def get_recommended_fix(self, error_type_or_msg: str) -> Optional[Dict[str, Any]]:
        errors = self._load_errors()
        for err in errors:
            if err["error_type"].lower() in error_type_or_msg.lower() or err["cause"].lower() in error_type_or_msg.lower():
                return err
        return {
            "error_type": error_type_or_msg,
            "cause": "Import or module resolution path mismatch",
            "recommended_fix": "Use absolute package import and verify sys.path",
            "occurrences": 1
        }


global_error_feedback_engine = ErrorFeedbackEngine()
