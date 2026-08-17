import io
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.services.project_exporter")

EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".git",
    "node_modules",
    ".DS_Store",
    "Thumbs.db",
    ".venv",
    "venv"
]


class ProjectExporter:
    """
    ProjectExporter packages the validated software project directory or files map into a ZIP archive.
    - Excludes cache folders, environment paths, node_modules, and git folders.
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
        if not str(target_zip_path).startswith(str(base_path)):
            raise ValueError(f"Unsafe export ZIP path: {target_zip_path}")

        # Ensure base directory exists
        base_path.mkdir(parents=True, exist_ok=True)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel_path, content in files_map.items():
                clean_rel = rel_path.replace("\\", "/").lstrip("/")

                # Filter out excluded directory segments
                parts = clean_rel.split("/")
                if any(p in EXCLUDE_PATTERNS for p in parts) or ".." in parts:
                    continue

                archive_path = f"{safe_name}/{clean_rel}"
                zf.writestr(archive_path, content or "")

        zip_bytes = buffer.getvalue()
        target_zip_path.write_bytes(zip_bytes)

        logger.info(f"[EXPORTER] Project ZIP archive created safely at {target_zip_path} ({len(zip_bytes)} bytes).")
        return target_zip_path


# Global ProjectExporter Instance
global_project_exporter = ProjectExporter()
