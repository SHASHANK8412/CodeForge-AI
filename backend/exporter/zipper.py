import io
import re
import zipfile
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("aiforge.exporter.zipper")

# What never goes into an exported project: dependency, build and cache folders, and local
# secrets / environment files. Example env files (.env.example) are kept, since they document
# the variables without holding values.
EXCLUDED_DIRS = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git", "node_modules",
    ".venv", "venv", ".aiforge_checkpoints", ".aws", ".ssh",
}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db", ".npmrc", ".pypirc", ".netrc", "id_rsa", "id_ed25519", "id_ecdsa"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pem", ".key", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3"}
_ENV_FILE = re.compile(r"^\.env(\..+)?$")
_ENV_TEMPLATE = re.compile(r"^\.env\.(example|sample|template|dist)$")


def export_exclusion_reason(rel_path: str) -> Optional[str]:
    """Why a project file is left out of an export, or None if it is exported."""
    parts = [p for p in rel_path.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        return "empty path"
    if ".." in parts or ":" in parts[0] or rel_path.startswith(("/", "\\", "~")):
        return "path outside the project"
    if any(p in EXCLUDED_DIRS for p in parts[:-1]):
        return "dependency/cache folder"
    name = parts[-1]
    if _ENV_FILE.match(name) and not _ENV_TEMPLATE.match(name):
        return "local environment file (may hold secrets)"
    if name in EXCLUDED_FILES or Path(name).suffix.lower() in EXCLUDED_SUFFIXES:
        return "secret, binary or local data file"
    return None


class ProjectZipper:
    """
    ProjectZipper compresses generated project directory structure and files into a ZIP archive.
    Every AIForge export goes through it, so the exclusion policy above applies everywhere.
    """

    def create_zip_bytes(self, project_files: Dict[str, str], root_folder: str = "project") -> bytes:
        """Compresses file dictionary into an in-memory ZIP archive bytes buffer."""
        buffer = io.BytesIO()
        skipped = 0

        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel_path, content in project_files.items():
                # Zip Slip / traversal paths are dropped, not "cleaned" into another location.
                if export_exclusion_reason(rel_path):
                    skipped += 1
                    continue
                clean_rel_path = "/".join(p for p in rel_path.replace("\\", "/").split("/") if p not in ("", "."))
                zf.writestr(f"{root_folder}/{clean_rel_path}" if root_folder else clean_rel_path, content or "")

        buffer.seek(0)
        zip_bytes = buffer.getvalue()
        logger.info(f"ProjectZipper created ZIP archive: {len(zip_bytes)} bytes across {len(project_files) - skipped} files "
                    f"({skipped} excluded)")
        return zip_bytes

    def save_zip_file(self, project_files: Dict[str, str], target_zip_path: str, root_folder: str = "project") -> str:
        """Saves ZIP archive to a file path on disk."""
        zip_bytes = self.create_zip_bytes(project_files, root_folder=root_folder)
        path = Path(target_zip_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(zip_bytes)
        return str(path)


# Global ProjectZipper Instance
global_project_zipper = ProjectZipper()
