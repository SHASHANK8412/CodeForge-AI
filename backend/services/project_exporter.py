import logging
from pathlib import Path
from typing import Dict

from backend.exporter.zipper import EXCLUDED_DIRS as EXCLUDE_PATTERNS  # noqa: F401 - kept for importers
from backend.exporter.zipper import global_project_zipper

logger = logging.getLogger("aiforge.services.project_exporter")


class ProjectExporter:
    """
    ProjectExporter packages the validated software project directory or files map into a ZIP archive.
    - Uses the shared export policy (backend/exporter/zipper.py): no caches, virtualenvs,
      node_modules, .git, .env files, keys or local databases.
    - Resolves path names safely and guards against path traversal vulnerabilities.
    """

    def export_project(
        self,
        project_name: str,
        files_map: Dict[str, str],
        base_dir: str = "generated_projects"
    ) -> Path:
        logger.info(f"[EXPORTER] Starting export for project: {project_name}")

        safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in project_name]).strip("_") or "AIForgeProject"
        base_path = Path(base_dir).resolve()
        target_zip_path = (base_path / f"AIForge_Project_{safe_name}.zip").resolve()

        # Path safety check
        if not Path(target_zip_path).is_relative_to(base_path):
            raise ValueError(f"Unsafe export ZIP path: {target_zip_path}")

        # Ensure base directory exists
        base_path.mkdir(parents=True, exist_ok=True)

        zip_bytes = global_project_zipper.create_zip_bytes(files_map, root_folder=safe_name)
        target_zip_path.write_bytes(zip_bytes)

        logger.info(f"[EXPORTER] Project ZIP archive created safely at {target_zip_path} ({len(zip_bytes)} bytes).")
        return target_zip_path


# Global ProjectExporter Instance
global_project_exporter = ProjectExporter()
