import re
import json
import logging
from typing import Dict, Any, List

from backend.quality.analyzer import global_code_analyzer
from backend.quality.security import global_security_scanner
from backend.quality.optimizer import global_performance_optimizer
from backend.quality.duplicate_detector import global_duplicate_detector
from backend.quality.metrics import global_quality_score_calculator

logger = logging.getLogger("aiforge.quality.report_generator")


class QualityReportGenerator:
    """
    QualityReportGenerator runs full quality assurance analysis across project files
    and provides automatic code fixes (Auto-Fix Pipeline).
    """

    def generate_full_report(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        """Executes full quality suite and returns structured report dict."""
        analysis = global_code_analyzer.analyze_project(project_files)
        security = global_security_scanner.scan_files(project_files)
        performance = global_performance_optimizer.analyze_performance(project_files)
        duplicates = global_duplicate_detector.detect_duplicates(project_files)

        has_doc = any("README.md" in k for k in project_files)
        scores = global_quality_score_calculator.calculate_scores(analysis, security, performance, has_doc)

        report = {
            "scores": scores,
            "analysis": analysis,
            "security": security,
            "performance": performance,
            "duplicates": duplicates
        }
        logger.info(f"Generated Quality Report with Overall Score: {scores['overall_score']}/100")
        return report

    def apply_autofix(self, project_files: Dict[str, str]) -> Dict[str, str]:
        """Auto-Fix Pipeline: Cleans trailing whitespace, removes redundant empty lines, and formats headers."""
        fixed_files = {}
        fixed_count = 0

        for path, content in project_files.items():
            fixed_content = content

            # 1. Clean trailing whitespace & duplicate newlines
            fixed_content = re.sub(r"[ \t]+\n", "\n", fixed_content)
            fixed_content = re.sub(r"\n{3,}", "\n\n", fixed_content)

            # 2. Add header formatting if missing in Python files
            if path.endswith(".py") and not fixed_content.startswith("#"):
                fixed_content = f"# AIForge Auto-Formatted Module: {path}\n" + fixed_content
                fixed_count += 1

            fixed_files[path] = fixed_content

        logger.info(f"Auto-Fix Pipeline processed {len(project_files)} files (Applied fixes to {fixed_count} files)")
        return fixed_files


# Global QualityReportGenerator Instance
global_quality_report_generator = QualityReportGenerator()
