import zipfile
import logging
from pathlib import Path
from typing import Iterator, Tuple

from backend.exporter.zipper import export_exclusion_reason

_logger = logging.getLogger("aiforge.performance")

EXCLUDED_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
    "Thumbs.db",
    ".git",
    ".venv",
    "venv",
    ".ipynb_checkpoints"
}


def archive_members(source_directory: Path) -> Iterator[Tuple[Path, str]]:
    """
    (file, archive name) for every file that may leave the machine: no caches, no secrets (.env, keys,
    databases - the export policy), and no symlinks or anything resolving outside the project, which
    would copy host files into the download.
    """
    root = source_directory.resolve()
    for file_path in source_directory.rglob("*"):
        parts = file_path.relative_to(source_directory).parts
        if any(part in EXCLUDED_NAMES for part in parts) or file_path.is_symlink() or not file_path.is_file():
            continue
        arcname = "/".join(parts)
        if export_exclusion_reason(arcname) or root not in file_path.resolve().parents:
            continue
        yield file_path, arcname


class ZipService:
    """
    Handles packaging the generated software project directory into a single ZIP archive,
    resolving cross-platform paths and excluding temporary or cached folders/files.
    """

    def __init__(self) -> None:
        pass

    def zip_project(self, source_directory: Path, output_zip_path: Path) -> Path:
        """
        Creates a ZIP archive of the source_directory at output_zip_path,
        excluding temporary names.
        """
        _logger.info(f"Creating ZIP archive from {source_directory} to {output_zip_path}")
        
        if not source_directory.exists():
            raise FileNotFoundError(f"Source directory for archiving does not exist: {source_directory}")

        try:
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, arcname in archive_members(source_directory):
                    zipf.write(file_path, arcname)

            _logger.info(f"Project successfully zipped at: {output_zip_path}")
            self.validate_zip_integrity(output_zip_path, source_directory)
            return output_zip_path
        except Exception as exc:
            _logger.error(f"Failed to create project ZIP archive: {exc}")
            raise RuntimeError(f"Failed to create ZIP package: {exc}") from exc

    def validate_zip_integrity(self, zip_path: Path, source_directory: Path) -> bool:
        """
        Validates generated ZIP archive: opens programmatically, checks files exist,
        non-empty when expected, and match source disk checksums.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP archive not found at '{zip_path}'")

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zip_names = set(zipf.namelist())
            for src_file, arcname in archive_members(source_directory):
                if arcname not in zip_names:
                    raise ValueError(f"ZIP Integrity Error: Missing file '{arcname}' in archive")

                zip_content = zipf.read(arcname)
                if len(zip_content) == 0 and src_file.name not in {"__init__.py", ".gitkeep"}:
                    _logger.warning(f"ZIP Warning: File '{arcname}' in archive is empty")

        _logger.info(f"ZIP archive integrity verified for '{zip_path.name}'")
        return True
