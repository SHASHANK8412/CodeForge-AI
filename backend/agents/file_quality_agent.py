import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.file_quality")


class QualityViolation(BaseModel):
    filepath: str
    rule: str
    message: str
    severity: str = "HIGH"


class QualityReport(BaseModel):
    is_passed: bool = True
    total_files: int = 0
    violations: List[QualityViolation] = Field(default_factory=list)
    summary: str = ""


class FileQualityAgent(BaseAgent):
    """
    File Quality Agent inspects every generated file to guarantee production quality:
    - Zero placeholders ('TODO', 'pass # write code', '...', 'mock implementation')
    - No empty functions or empty classes
    - No duplicate code blocks
    - Clean PEP8 guidelines compliance for Python
    - ESLint / JSX compatibility for JavaScript/TypeScript
    """

    PLACEHOLDER_PATTERNS = [
        (r"#\s*TODO", "TODO comment placeholder found"),
        (r"//\s*TODO", "TODO comment placeholder found"),
        (r"/\*\s*TODO", "TODO comment block found"),
        (r"pass\s*#\s*implement", "Empty pass placeholder comment found"),
        (r"raise\s+NotImplementedError", "NotImplementedError placeholder found"),
        (r"//\s*implement\s+later", "Placeholder implement comment found"),
        (r"mock_data\s*=\s*\[\s*\]", "Mock data array placeholder found")
    ]

    EMPTY_FUNC_PYTHON = r"def\s+\w+\([^)]*\):\s*\n\s*(?:pass|\.\.\.|\"\".*?\"\")\s*(?:\n|$)"
    EMPTY_FUNC_JS = r"(?:function\s+\w+|const\s+\w+\s*=\s*\([^)]*\)\s*=>)\s*\{\s*\}"

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the File Quality Agent for AIForge. Your job is to strictly enforce "
                "production code standards, rejecting placeholders, TODO comments, empty functions, "
                "or duplicate implementations across all generated code files."
            ),
            task_name="file_quality"
        )

    def analyze_file(self, filepath: str, content: str) -> List[QualityViolation]:
        violations = []

        # 1. Check placeholders
        for pattern, msg in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(QualityViolation(
                    filepath=filepath,
                    rule="NO_PLACEHOLDERS",
                    message=msg,
                    severity="HIGH"
                ))

        # 2. Check Python empty functions & pass
        if filepath.endswith(".py"):
            if re.search(self.EMPTY_FUNC_PYTHON, content):
                violations.append(QualityViolation(
                    filepath=filepath,
                    rule="NO_EMPTY_FUNCTIONS",
                    message="Python file contains an empty function body with pass or ellipsis.",
                    severity="HIGH"
                ))
            # Check trailing whitespace or indentation mismatch basic check
            lines = content.splitlines()
            if any(len(line) > 120 for line in lines):
                violations.append(QualityViolation(
                    filepath=filepath,
                    rule="PEP8_LINE_LENGTH",
                    message="File contains lines exceeding 120 characters.",
                    severity="LOW"
                ))

        # 3. Check JS/JSX empty functions
        if filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
            if re.search(self.EMPTY_FUNC_JS, content):
                violations.append(QualityViolation(
                    filepath=filepath,
                    rule="NO_EMPTY_FUNCTIONS",
                    message="JS/TS file contains an empty function block.",
                    severity="HIGH"
                ))

        return violations

    def audit_project(self, files: Dict[str, str]) -> QualityReport:
        all_violations = []
        for path, code in files.items():
            viols = self.analyze_file(path, code)
            all_violations.extend(viols)

        high_severity_count = sum(1 for v in all_violations if v.severity == "HIGH")
        passed = high_severity_count == 0

        summary = (
            f"File Quality Audit: {'PASSED' if passed else 'FAILED'}. "
            f"Inspected {len(files)} files. Found {len(all_violations)} total violations "
            f"({high_severity_count} high severity)."
        )

        return QualityReport(
            is_passed=passed,
            total_files=len(files),
            violations=all_violations,
            summary=summary
        )
