import time
import os
import logging
from pathlib import Path
from typing import List
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files, get_process_metrics

_logger = logging.getLogger("aiforge.performance")

class PerformanceChecker:
    """
    Measures codebase size metrics (files scanned, lines of code, largest files) and
    compiles validation execution performance (slowest validator, validation time, memory/CPU).
    """

    def validate(self, project_path: Path) -> ValidationResult:
        """
        Runs static performance scan on files (LOC, counts, largest files).
        """
        start_time = time.perf_counter()
        _logger.info("Performance Checker Started")

        errors = []
        warnings = []
        suggestions = []
        
        all_files = list(get_all_files(project_path, [".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".sql", ".json"]))
        
        total_files = len(all_files)
        total_loc = 0
        file_sizes = [] # list of tuple: (filename, size_bytes, lines)
        
        for file_path in all_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                lines = len(content.splitlines())
                total_loc += lines
                size = file_path.stat().st_size
                file_sizes.append((str(file_path.relative_to(project_path)), size, lines))
            except Exception:
                pass
                
        # Find largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        largest_files = file_sizes[:5]
        
        for name, size, lines in largest_files:
            if lines > 300:
                warnings.append(f"Oversized file '{name}' has {lines} lines (>{size} bytes)")
                suggestions.append(f"Consider splitting module '{name}' to follow single responsibility principle")

        # Basic suggestions based on code metrics
        if total_loc > 5000:
            suggestions.append("Project size is large; consider implementing modular sub-packages or lazy loading")
            
        sys_metrics = get_process_metrics()
        
        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(warnings) * 3
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"

        _logger.info(f"Performance Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Performance Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "total_files": total_files,
                "total_loc": total_loc,
                "largest_files": [
                    {"file": name, "size_kb": round(size / 1024, 2), "lines": lines}
                    for name, size, lines in largest_files
                ],
                "suggestions": suggestions,
                "memory_mb": sys_metrics["memory_mb"],
                "cpu_percent": sys_metrics["cpu_percent"]
            }
        )

    def compile_summary_metrics(self, results: List[ValidationResult], total_duration: float) -> dict:
        """
        Compiles execution summary across all validators.
        """
        slowest_name = "None"
        slowest_time = 0.0
        
        for r in results:
            if r.execution_time > slowest_time:
                slowest_time = r.execution_time
                slowest_name = r.validator
                
        sys_metrics = get_process_metrics()
        
        suggestions = []
        if slowest_time > 1.0:
            suggestions.append(f"Slowest validator is '{slowest_name}' ({slowest_time:.2f}s). Consider caching checks for unchanged folders.")
        if sys_metrics["memory_mb"] > 200:
            suggestions.append("Process memory footprint is high. Optimize file buffering during file system scans.")
            
        return {
            "total_validation_time": round(total_duration, 4),
            "average_validation_time": round(total_duration / max(1, len(results)), 4),
            "slowest_validator": slowest_name,
            "slowest_validator_time": slowest_time,
            "memory_usage_mb": sys_metrics["memory_mb"],
            "cpu_usage_percent": sys_metrics["cpu_percent"],
            "suggestions": suggestions
        }
