"""
AIForge V2 – Documentation Report Validator Gate
================================================
Validates completeness, markdown formatting, and diagram validity of generated DocumentationReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.documentation.models import DocumentationReport

_logger = logging.getLogger("aiforge.v2.documentation.validator")


class DocumentationValidator:

    def validate_report(self, report: DocumentationReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name:
            issues.append("Project name is missing.")

        if not report.readme_markdown or len(report.readme_markdown) < 50:
            issues.append("README.md content is missing or incomplete.")

        if not report.developer_docs_markdown or len(report.developer_docs_markdown) < 50:
            issues.append("DEVELOPER_GUIDE.md content is missing or incomplete.")

        if len(report.diagrams) < 1:
            issues.append("No Mermaid architecture diagrams generated.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"DocumentationValidator: Documentation package for '{report.project_name}' PASSED validation gate.")
        else:
            _logger.warning(f"DocumentationValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_documentation_validator = DocumentationValidator()
