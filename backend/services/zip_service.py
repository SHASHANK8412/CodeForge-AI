import shutil
import logging
from pathlib import Path

_logger = logging.getLogger("aiforge.performance")


class ZipService:
    """
    Handles packaging the generated software project directory into a single ZIP archive,
    resolving cross-platform paths across Windows, macOS, and Linux.
    """

    def __init__(self) -> None:
        pass

    def zip_project(self, source_directory: Path, output_zip_path: Path) -> Path:
        """
        Creates a ZIP archive of the source_directory at output_zip_path (without the .zip extension in the base name).
        Returns the path to the generated ZIP file.
        """
        _logger.info(f"Creating ZIP archive from {source_directory} to {output_zip_path}")
        
        if not source_directory.exists():
            raise FileNotFoundError(f"Source directory for archiving does not exist: {source_directory}")

        # Resolve output zip base path (shutil.make_archive adds .zip automatically)
        zip_base = output_zip_path.with_suffix("")

        try:
            shutil.make_archive(
                base_name=str(zip_base),
                format="zip",
                root_dir=str(source_directory)
            )
            created_zip = output_zip_path.with_name(f"{output_zip_path.name}")
            _logger.info(f"Project successfully zipped at: {created_zip}")
            return created_zip
        except Exception as exc:
            _logger.error(f"Failed to create project ZIP archive: {exc}")
            raise RuntimeError(f"Failed to create ZIP package: {exc}") from exc
