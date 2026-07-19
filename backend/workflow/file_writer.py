import os
import logging
from pathlib import Path

_logger = logging.getLogger("aiforge.performance")


def create_project_directories(base_path: Path, relative_paths: list[str]) -> None:
    """
    Creates multiple subdirectories under the base path.
    """
    for rel_path in relative_paths:
        dir_path = base_path / rel_path
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            _logger.info(f"Directory created: {dir_path}")
        except Exception as exc:
            _logger.error(f"Failed to create directory {dir_path}: {exc}")
            raise


def write_project_file(file_path: Path, content: str) -> None:
    """
    Writes content string to the specified file path, creating parent folders if needed.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        _logger.info(f"File written successfully: {file_path}")
    except Exception as exc:
        _logger.error(f"Failed to write file {file_path}: {exc}")
        raise
