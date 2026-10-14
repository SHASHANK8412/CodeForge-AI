"""
AIForge Benchmark Lab — Persistent Storage
==========================================
Persists benchmark configurations, runs, and artifacts to disk with strict
path sanitization and authorization boundaries.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.benchmark_lab.models import BenchmarkRun

_logger = logging.getLogger("aiforge.benchmark_lab.store")

STORE_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "data" / "benchmark_lab"
STORE_FILE = STORE_DIR / "runs.json"
RUNS_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "runs"


class BenchmarkStore:
    """
    Handles local persistence of benchmark runs and secure retrieval of generated artifacts.
    """

    def __init__(self) -> None:
        STORE_DIR.mkdir(parents=True, exist_ok=True)
        RUNS_BASE_DIR.mkdir(parents=True, exist_ok=True)
        self._runs_cache: Dict[str, BenchmarkRun] = {}
        self._load()

    def _load(self) -> None:
        if STORE_FILE.exists():
            try:
                data = json.loads(STORE_FILE.read_text(encoding="utf-8"))
                for r_data in data:
                    run = BenchmarkRun(**r_data)
                    self._runs_cache[run.id] = run
            except Exception as e:
                _logger.warning(f"Could not load historical benchmark runs: {e}")

    def _save(self) -> None:
        try:
            serialized = [r.model_dump() for r in self._runs_cache.values()]
            STORE_FILE.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"Failed to persist benchmark runs to file: {e}")

    def save_run(self, run: BenchmarkRun) -> BenchmarkRun:
        self._runs_cache[run.id] = run
        self._save()
        return run

    def get_run(self, run_id: str) -> Optional[BenchmarkRun]:
        return self._runs_cache.get(run_id)

    def list_runs(self) -> List[BenchmarkRun]:
        # Return sorted by created_at descending
        return sorted(self._runs_cache.values(), key=lambda r: r.created_at, reverse=True)

    def get_artifact_content(self, run_id: str, task_id: str, config_id: str, filename: str) -> Optional[str]:
        """
        Safely retrieves generated artifact content while preventing directory traversal attacks.
        """
        # Guard against directory traversal
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            _logger.warning(f"Security: Blocked potential path traversal attempt: '{filename}'")
            return None

        # Look in matching run directories
        run_folder = RUNS_BASE_DIR / run_id
        if not run_folder.exists():
            return None

        # Find matching task_config folder
        candidates = list(run_folder.glob(f"{task_id}_{config_id}*"))
        if not candidates:
            # Fallback check any folder containing task_id
            candidates = list(run_folder.glob(f"{task_id}*"))

        for cand in candidates:
            target_file = cand / filename
            try:
                # Resolve to ensure it stays strictly within run_folder
                resolved = target_file.resolve()
                if resolved.is_relative_to(run_folder.resolve()) and resolved.is_file():
                    return resolved.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        return None


global_benchmark_store = BenchmarkStore()
