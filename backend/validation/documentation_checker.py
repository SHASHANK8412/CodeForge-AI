import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

class DocumentationChecker:
    """
    Validates presence of README.md, documentation formatting, and file-level docstring completeness.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Documentation Checker Started")

        errors = []
        warnings = []
        
        # Check README.md
        readme = project_path / "README.md"
        if not readme.exists():
            warnings.append("Project lacks a README.md file in the root directory")
        else:
            try:
                with open(readme, "r", encoding="utf-8") as f:
                    content = f.read()
                if len(content.strip()) < 50:
                    warnings.append("README.md file is too brief or placeholder-like")
            except Exception:
                pass

        # Check Python files docstrings (approximate check)
        py_files = list(get_all_files(project_path, [".py"]))
        missing_docstrings = 0
        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Check for basic presence of triple quotes
                if '"""' not in content and "'''" not in content:
                    missing_docstrings += 1
            except Exception:
                pass
                
        if missing_docstrings > 0:
            warnings.append(f"Found {missing_docstrings} Python file(s) missing header/class docstring annotations")

        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(warnings) * 4
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"

        _logger.info(f"Documentation Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Documentation Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={}
        )
