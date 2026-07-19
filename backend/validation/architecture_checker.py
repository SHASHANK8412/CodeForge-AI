import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

class ArchitectureChecker:
    """
    Validates project structure, architecture formatting, and layout compliance.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Architecture Checker Started")

        errors = []
        warnings = []
        
        # Verify required base folders
        required_dirs = ["backend", "frontend", "database"]
        for directory in required_dirs:
            p = project_path / directory
            if not p.exists() or not p.is_dir():
                warnings.append(f"Missing recommended root directory: '{directory}'")

        # Verify configuration layouts
        config_files = ["docker-compose.yml", "README.md", ".gitignore", ".env.example"]
        for file in config_files:
            p = project_path / file
            if not p.exists():
                warnings.append(f"Missing standard root config file: '{file}'")

        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(warnings) * 5
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"

        _logger.info(f"Architecture Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Architecture Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={}
        )
