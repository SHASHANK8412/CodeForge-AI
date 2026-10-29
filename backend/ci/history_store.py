"""
AIForge CI Pipeline Run History Store
====================================
Maintains execution history of CI pipeline runs per project.
Supports in-memory caching and persistent logging.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.ci.models import CIPipelineResult, CIRunHistoryItem

_logger = logging.getLogger("aiforge.ci.history_store")


class CIHistoryStore:
    """
    Store for historical CI pipeline runs.
    """

    def __init__(self, storage_dir: Optional[Path] = None, storage_path: Optional[Path] = None):
        self._runs_by_id: Dict[str, CIPipelineResult] = {}
        self._history_by_project: Dict[str, List[CIRunHistoryItem]] = {}
        effective = storage_dir or storage_path or (Path(__file__).resolve().parents[2] / "logs" / "ci_runs")
        self.storage_dir = effective.parent if effective.suffix else effective
        self._load_existing_runs()

    def _load_existing_runs(self) -> None:
        if not self.storage_dir.exists():
            return
        for file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                res = CIPipelineResult(**data)
                self._runs_by_id[res.run_id] = res
                if res.project_id not in self._history_by_project:
                    self._history_by_project[res.project_id] = []
                summaries = {st.stage: st.status for st in res.stages}
                item = CIRunHistoryItem(
                    run_id=res.run_id,
                    project_id=res.project_id,
                    timestamp=res.created_at,
                    commit_version=res.commit_version,
                    overall_status=res.status,
                    repair_attempts=res.repair_attempts,
                    duration=res.duration,
                    stage_summaries=summaries,
                    backend_used=res.backend_used
                )
                self._history_by_project[res.project_id].append(item)
            except Exception:
                pass

    def save_run(self, result: CIPipelineResult) -> None:
        """Saves a CI pipeline run to store and writes backup JSON."""
        self._runs_by_id[result.run_id] = result

        summaries = {}
        for st in result.stages:
            summaries[st.stage] = st.status

        item = CIRunHistoryItem(
            run_id=result.run_id,
            project_id=result.project_id,
            timestamp=result.created_at,
            commit_version=result.commit_version,
            overall_status=result.status,
            repair_attempts=result.repair_attempts,
            duration=result.duration,
            stage_summaries=summaries,
            backend_used=result.backend_used
        )

        if result.project_id not in self._history_by_project:
            self._history_by_project[result.project_id] = []
        # Prepend latest run to history
        self._history_by_project[result.project_id].insert(0, item)

        # Persist to disk
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            run_file = self.storage_dir / f"{result.run_id}.json"
            run_file.write_text(json.dumps(result.model_dump(), indent=2), encoding="utf-8")
        except Exception as e:
            _logger.debug(f"Could not persist run to disk: {e}")

    def get_history(self, project_id: str) -> List[CIRunHistoryItem]:
        """Returns history list for a project, newest first."""
        return self._history_by_project.get(project_id, [])

    def get_runs(self, project_id: str) -> List[CIRunHistoryItem]:
        """Alias for get_history."""
        return self.get_history(project_id)

    def get_run(self, run_id: str) -> Optional[CIPipelineResult]:
        """Returns full run record by run ID."""
        if run_id in self._runs_by_id:
            return self._runs_by_id[run_id]

        # Try disk fallback
        try:
            run_file = self.storage_dir / f"{run_id}.json"
            if run_file.exists():
                data = json.loads(run_file.read_text(encoding="utf-8"))
                return CIPipelineResult(**data)
        except Exception:
            pass

        return None

    def get_run_by_id(self, run_id: str) -> Optional[CIPipelineResult]:
        """Alias for get_run."""
        return self.get_run(run_id)

    def clear(self, project_id: Optional[str] = None) -> None:
        if project_id:
            self._history_by_project.pop(project_id, None)
            self._runs_by_id = {k: v for k, v in self._runs_by_id.items() if v.project_id != project_id}
        else:
            self._runs_by_id.clear()
            self._history_by_project.clear()


global_ci_history_store = CIHistoryStore()
