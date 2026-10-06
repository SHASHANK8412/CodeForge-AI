"""
AIForge Rollback Manager
========================
Checkpoints a project directory before deployment and restores it when a deploy fails
health checks or smoke tests.

Checkpoints are full copies stored next to the project, in
<parent>/.aiforge_checkpoints/<project-name>/<tag>/, so they survive restarts and are
never nested inside the tree they snapshot.
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.workspace.notifications import global_notification_manager

_logger = logging.getLogger("aiforge.deployment.rollback")

CHECKPOINT_DIRNAME = ".aiforge_checkpoints"
_SKIP = shutil.ignore_patterns("node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build")


class RollbackManager:
    """Creates real file checkpoints and restores them on failure."""

    def __init__(self) -> None:
        self.rollback_history: List[Dict[str, Any]] = []

    @staticmethod
    def _checkpoint_root(project_path: Path) -> Path:
        project_path = Path(project_path).resolve()
        return project_path.parent / CHECKPOINT_DIRNAME / project_path.name

    def list_checkpoints(self, project_path: Any) -> List[str]:
        root = self._checkpoint_root(project_path)
        return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []

    def create_deployment_checkpoint(self, project_path: Any = None) -> str:
        """Copy the project directory into a new checkpoint and return its tag."""
        tag = f"deploy-checkpoint-{time.time_ns() // 1_000_000}"
        if project_path is None or not Path(project_path).is_dir():
            _logger.warning("RollbackManager: no project directory to checkpoint (%s)", project_path)
            return tag
        dest = self._checkpoint_root(project_path) / tag
        shutil.copytree(project_path, dest, ignore=_SKIP)
        _logger.info("RollbackManager: checkpoint %s created at %s", tag, dest)
        return tag

    def trigger_rollback(
        self,
        reason: str = "Health Check Failure",
        failed_version: Optional[str] = None,
        target_version: Optional[str] = None,
        project_path: Any = None,
    ) -> Dict[str, Any]:
        """Restore target_version (a checkpoint tag) or the newest checkpoint into project_path."""
        restored: Optional[str] = None
        status = "NO_CHECKPOINT"
        if project_path is not None and Path(project_path).is_dir():
            checkpoints = self.list_checkpoints(project_path)
            pick = target_version if target_version in checkpoints else (checkpoints[-1] if checkpoints else None)
            if pick:
                self._restore(Path(project_path), self._checkpoint_root(project_path) / pick)
                restored, status = pick, "RESTORED"

        entry = {
            "rollback_id": f"rb_{time.time_ns() // 1_000_000}",
            "trigger_reason": reason,
            "failed_version": failed_version,
            "restored_version": restored,
            "status": status,
            "timestamp": time.time(),
        }
        self.rollback_history.insert(0, entry)
        self._write_rollback_log(entry)

        if status == "RESTORED":
            global_notification_manager.notify(
                event_type="deployment_rollback",
                project_id=Path(project_path).name,
                project_name=Path(project_path).name,
                title=f"Automated rollback restored {restored}",
                message=f"Rolled back because: {reason}",
            )
            _logger.warning("RollbackManager: restored %s into %s (reason: %s)", restored, project_path, reason)
        else:
            _logger.error("RollbackManager: rollback requested (%s) but no checkpoint exists for %s", reason, project_path)
        return entry

    @staticmethod
    def _restore(project_path: Path, checkpoint: Path) -> None:
        for child in project_path.iterdir():
            if child.name in ("node_modules", ".git", ".venv", "venv"):
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        shutil.copytree(checkpoint, project_path, dirs_exist_ok=True)

    def rollback_to_checkpoint(self, project_path: Any = None, target_version: Optional[str] = None) -> Optional[str]:
        res = self.trigger_rollback(reason="User initiated rollback", target_version=target_version, project_path=project_path)
        return res.get("restored_version")

    def get_rollback_history(self) -> List[Dict[str, Any]]:
        return list(self.rollback_history)

    def _write_rollback_log(self, entry: Dict[str, Any]) -> None:
        try:
            log_dir = Path(__file__).resolve().parents[2] / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "rollback.log", "a", encoding="utf-8") as f:
                f.write(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} [ROLLBACK] ID: {entry['rollback_id']} | "
                    f"Status: {entry['status']} | Restored: {entry['restored_version']} | Reason: {entry['trigger_reason']}\n"
                )
        except OSError as e:
            _logger.error(f"Failed writing to rollback.log: {e}")


global_rollback_manager = RollbackManager()
