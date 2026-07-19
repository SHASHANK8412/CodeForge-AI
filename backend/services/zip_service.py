import zipfile
import logging
from pathlib import Path

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
                for file_path in source_directory.rglob("*"):
                    # Check if any parent folder or the file itself is in EXCLUDED_NAMES
                    parts = file_path.relative_to(source_directory).parts
                    if any(part in EXCLUDED_NAMES for part in parts):
                        continue
                    
                    if file_path.is_file():
                        arcname = str(file_path.relative_to(source_directory))
                        zipf.write(file_path, arcname)

            _logger.info(f"Project successfully zipped at: {output_zip_path}")
            return output_zip_path
        except Exception as exc:
            _logger.error(f"Failed to create project ZIP archive: {exc}")
            raise RuntimeError(f"Failed to create ZIP package: {exc}") from exc
