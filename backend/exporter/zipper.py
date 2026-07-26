import io
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("aiforge.exporter.zipper")


class ProjectZipper:
    """
    ProjectZipper compresses generated project directory structure and files into a ZIP archive.
    """

    def create_zip_bytes(self, project_files: Dict[str, str], root_folder: str = "project") -> bytes:
        """Compresses file dictionary into an in-memory ZIP archive bytes buffer."""
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel_path, content in project_files.items():
                archive_path = f"{root_folder}/{rel_path.lstrip('/')}"
                zf.writestr(archive_path, content)

        buffer.seek(0)
        zip_bytes = buffer.getvalue()
        logger.info(f"ProjectZipper created ZIP archive: {len(zip_bytes)} bytes across {len(project_files)} files")
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
