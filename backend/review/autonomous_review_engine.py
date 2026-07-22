"""
Day 44 - Autonomous AI Code Review & Refactoring Engine
=========================================================
Engine performing multi-dimensional code auditing:
- File-by-file static analysis across Python, JavaScript, SQL, HTML
- Detection of Code Smells, Performance Bottlenecks, and Security Vulnerabilities
- Automatic code refactoring with AST functionality preservation
- Unified diff generation showing before/after refactoring changes
- Quality scoring (0-100 & Letter Grades)
- JSON and Markdown review reports
"""

import ast
import re
import difflib
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

_logger = logging.getLogger("aiforge.review_engine")


@dataclass
class DiagnosticFinding:
    category: str  # code_smell, performance, security
    severity: str  # Critical, Warning, Info
    file: str
    line: int
    issue: str
    recommendation: str
    auto_fixable: bool = True


@dataclass
class FileReviewResult:
    filename: str
    original_code: str
    refactored_code: str
    diff: str
    findings: List[DiagnosticFinding]
    quality_score: float  # 0.0 - 100.0


class CodeSmellScanner:
    """Scans code files for code smells and maintainability anti-patterns."""

    def scan(self, filename: str, code: str) -> List[DiagnosticFinding]:
        findings = []
        lines = code.splitlines()

        # 1. Unused imports in Python
        if filename.endswith(".py"):
            unused_import_match = re.findall(r"^\s*import\s+([a-zA-Z0-9_]+)\s*$", code, re.MULTILINE)
            for imp in unused_import_match:
                if imp not in ["sys", "os", "json", "typing"] and code.count(imp) == 1:
                    findings.append(DiagnosticFinding(
                        category="code_smell",
                        severity="Info",
                        file=filename,
                        line=1,
                        issue=f"Unused import detected: '{imp}'",
                        recommendation=f"Remove unused import '{imp}' to improve readability.",
                        auto_fixable=True
                    ))

        # 2. Long functions (>30 lines)
        for idx, line in enumerate(lines, 1):
            if re.match(r"^\s*(def|function|async def)\s+[a-zA-Z0-9_]+", line):
                # Count function length
                indent = len(line) - len(line.lstrip())
                func_length = 0
                for next_line in lines[idx:]:
                    if next_line.strip() and (len(next_line) - len(next_line.lstrip())) <= indent:
                        break
                    func_length += 1

                if func_length > 30:
                    func_name = line.strip().split("(")[0]
                    findings.append(DiagnosticFinding(
                        category="code_smell",
                        severity="Warning",
                        file=filename,
                        line=idx,
                        issue=f"Long function '{func_name}' ({func_length} lines)",
                        recommendation="Decompose large functions into smaller modular helper functions.",
                        auto_fixable=False
                    ))

        # 3. Missing type annotations in Python functions
        if filename.endswith(".py"):
            for idx, line in enumerate(lines, 1):
                if line.strip().startswith("def ") and "->" not in line and not line.strip().startswith("def __"):
                    findings.append(DiagnosticFinding(
                        category="code_smell",
                        severity="Info",
                        file=filename,
                        line=idx,
                        issue=f"Missing return type annotation: '{line.strip()}'",
                        recommendation="Add explicit return type hint annotations (e.g. -> Dict[str, Any]).",
                        auto_fixable=True
                    ))

        # 4. Deep nesting (>3 levels)
        for idx, line in enumerate(lines, 1):
            indent_level = (len(line) - len(line.lstrip())) // 4
            if indent_level > 4 and line.strip():
                findings.append(DiagnosticFinding(
                    category="code_smell",
                    severity="Warning",
                    file=filename,
                    line=idx,
                    issue=f"Deeply nested block (indentation level {indent_level})",
                    recommendation="Guard clauses or early returns to reduce nesting depth.",
                    auto_fixable=False
                ))

        return findings


class PerformanceScanner:
    """Scans code files for performance bottlenecks and blocking operations."""

    def scan(self, filename: str, code: str) -> List[DiagnosticFinding]:
        findings = []
        lines = code.splitlines()

        # 1. Blocking synchronous call inside async function
        if filename.endswith(".py"):
            in_async = False
            async_line_no = 0
            for idx, line in enumerate(lines, 1):
                if "async def " in line:
                    in_async = True
                    async_line_no = idx
                elif in_async and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    in_async = False

                if in_async:
                    if "time.sleep(" in line:
                        findings.append(DiagnosticFinding(
                            category="performance",
                            severity="Critical",
                            file=filename,
                            line=idx,
                            issue="Blocking 'time.sleep()' used inside async function",
                            recommendation="Replace 'time.sleep()' with non-blocking 'await asyncio.sleep()'.",
                            auto_fixable=True
                        ))
                    elif "requests.get(" in line or "requests.post(" in line:
                        findings.append(DiagnosticFinding(
                            category="performance",
                            severity="Warning",
                            file=filename,
                            line=idx,
                            issue="Synchronous HTTP call 'requests' inside async function",
                            recommendation="Use async HTTP client like 'httpx.AsyncClient' or 'aiohttp'.",
                            auto_fixable=True
                        ))

        # 2. Query inside loop (N+1 query pattern)
        for idx, line in enumerate(lines, 1):
            if any(k in line for k in ["for ", "while "]):
                # Check next 5 lines for DB query
                for next_idx, next_line in enumerate(lines[idx:idx+5], idx):
                    if any(q in next_line for q in ["select ", "query(", "execute(", ".find_one("]):
                        findings.append(DiagnosticFinding(
                            category="performance",
                            severity="Critical",
                            file=filename,
                            line=next_idx,
                            issue="N+1 database query detected inside loop",
                            recommendation="Batch database query outside loop using WHERE IN or JOIN clause.",
                            auto_fixable=False
                        ))
                        break

        return findings


class SecurityScanner:
    """Scans code files for security vulnerabilities and dangerous operations."""

    def scan(self, filename: str, code: str) -> List[DiagnosticFinding]:
        findings = []
        lines = code.splitlines()

        # 1. Hardcoded secrets & API keys
        secret_pattern = re.compile(
            r"(?i)\b(secret_key|api_key|token|password|passwd|private_key)\b\s*=\s*['\"]([^'\"]{8,})['\"]"
        )
        for idx, line in enumerate(lines, 1):
            match = secret_pattern.search(line)
            if match:
                val = match.group(2)
                if not any(ph in val.lower() for ph in ["env", "config", "placeholder", "your_", "jwt_token"]):
                    findings.append(DiagnosticFinding(
                        category="security",
                        severity="Critical",
                        file=filename,
                        line=idx,
                        issue=f"Hardcoded secret detected: '{match.group(0).strip()}'",
                        recommendation="Load secrets dynamically from environment via os.getenv().",
                        auto_fixable=True
                    ))

        # 2. SQL Injection risks
        sql_pattern = re.compile(r"(?i)\b(execute|select|insert|update|delete)\b.*f['\"].*\{")
        for idx, line in enumerate(lines, 1):
            if sql_pattern.search(line):
                findings.append(DiagnosticFinding(
                    category="security",
                    severity="Critical",
                    file=filename,
                    line=idx,
                    issue="Possible SQL Injection via f-string string interpolation in query",
                    recommendation="Use parameterized SQL queries with bind variables.",
                    auto_fixable=False
                ))

        # 3. Unsafe eval / exec / dangerouslySetInnerHTML
        for idx, line in enumerate(lines, 1):
            if "eval(" in line or "exec(" in line or "dangerouslySetInnerHTML" in line:
                findings.append(DiagnosticFinding(
                    category="security",
                    severity="Critical",
                    file=filename,
                    line=idx,
                    issue="Unsafe code execution or DOM injection ('eval', 'exec', or 'dangerouslySetInnerHTML')",
                    recommendation="Remove dynamic execution constructs and sanitize inputs.",
                    auto_fixable=False
                ))

        # 4. Wildcard CORS
        for idx, line in enumerate(lines, 1):
            if 'allow_origins=["*"]' in line or "allow_origins=['*']" in line:
                findings.append(DiagnosticFinding(
                    category="security",
                    severity="Warning",
                    file=filename,
                    line=idx,
                    issue="Wildcard CORS origins allow_origins=['*'] allows any origin",
                    recommendation="Restrict allowed origins to explicit trusted domain list.",
                    auto_fixable=True
                ))

        return findings


class AutoRefactorer:
    """Applies automatic refactoring patches while preserving AST syntax validity."""

    def refactor(self, filename: str, code: str, findings: List[DiagnosticFinding]) -> str:
        refactored = code

        # 1. Fix hardcoded secrets -> os.getenv
        secret_pattern = re.compile(
            r"(?i)\b(secret_key|api_key|token|password|passwd|private_key)\b\s*=\s*['\"]([^'\"]{8,})['\"]"
        )

        def replace_secret(match):
            var_name = match.group(1).upper()
            val = match.group(2)
            if any(ph in val.lower() for ph in ["env", "config", "placeholder", "your_", "jwt_token"]):
                return match.group(0)
            return f"{match.group(1)} = os.getenv('{var_name}', '{val}')"

        if filename.endswith(".py"):
            refactored = secret_pattern.sub(replace_secret, refactored)
            if "os.getenv" in refactored and "import os" not in refactored:
                refactored = "import os\n" + refactored

        # 2. Fix blocking time.sleep inside async def -> await asyncio.sleep
        if filename.endswith(".py"):
            if "time.sleep(" in refactored:
                refactored = refactored.replace("time.sleep(", "await asyncio.sleep(")
                if "import asyncio" not in refactored:
                    refactored = "import asyncio\n" + refactored

        # 3. Fix wildcard CORS allow_origins=["*"] -> restricted domains
        if 'allow_origins=["*"]' in refactored:
            refactored = refactored.replace('allow_origins=["*"]', 'allow_origins=["http://localhost:3000", "http://127.0.0.1:8000"]')
        elif "allow_origins=['*']" in refactored:
            refactored = refactored.replace("allow_origins=['*']", "allow_origins=['http://localhost:3000', 'http://127.0.0.1:8000']")

        # 4. AST Validation for Python files
        if filename.endswith(".py"):
            try:
                ast.parse(refactored)
            except Exception as e:
                _logger.warning(f"Refactoring created syntax error in {filename}, reverting: {e}")
                return code

        return refactored


class DiffEngine:
    """Generates clean unified diffs comparing original vs refactored code."""

    def generate_diff(self, filename: str, original: str, refactored: str) -> str:
        if original == refactored:
            return "No changes required."

        orig_lines = original.splitlines(keepends=True)
        ref_lines = refactored.splitlines(keepends=True)

        diff = difflib.unified_diff(
            orig_lines,
            ref_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=3
        )
        return "".join(diff)


class QualityScoreEngine:
    """Calculates weighted diagnostic quality scores and assigns letter grades."""

    def compute_score(self, findings: List[DiagnosticFinding]) -> Tuple[float, str, Dict[str, float]]:
        base_score = 100.0

        scores = {
            "readability": 25.0,
            "security": 25.0,
            "performance": 25.0,
            "maintainability": 25.0
        }

        for f in findings:
            deduction = 10.0 if f.severity == "Critical" else (5.0 if f.severity == "Warning" else 2.0)
            base_score -= deduction

            if f.category == "security":
                scores["security"] = max(0.0, scores["security"] - deduction)
            elif f.category == "performance":
                scores["performance"] = max(0.0, scores["performance"] - deduction)
            elif f.category == "code_smell":
                scores["maintainability"] = max(0.0, scores["maintainability"] - deduction)
                scores["readability"] = max(0.0, scores["readability"] - (deduction / 2))

        final_score = max(0.0, min(100.0, round(base_score, 1)))

        if final_score >= 95.0:
            grade = "A+"
        elif final_score >= 88.0:
            grade = "A"
        elif final_score >= 78.0:
            grade = "B"
        elif final_score >= 65.0:
            grade = "C"
        else:
            grade = "F"

        return final_score, grade, scores


class ReviewReportProducer:
    """Generates JSON and Markdown review reports."""

    def produce_json(self, overall_score: float, grade: str, file_results: List[FileReviewResult]) -> Dict[str, Any]:
        return {
            "overall_quality_score": overall_score,
            "grade": grade,
            "total_files_reviewed": len(file_results),
            "files": [
                {
                    "filename": fr.filename,
                    "quality_score": fr.quality_score,
                    "findings": [
                        {
                            "category": f.category,
                            "severity": f.severity,
                            "line": f.line,
                            "issue": f.issue,
                            "recommendation": f.recommendation,
                            "auto_fixable": f.auto_fixable
                        }
                        for f in fr.findings
                    ],
                    "diff": fr.diff
                }
                for fr in file_results
            ]
        }

    def produce_markdown(self, overall_score: float, grade: str, file_results: List[FileReviewResult]) -> str:
        md = []
        md.append("# 🔍 Autonomous AI Code Review & Refactoring Report\n")
        md.append(f"**Overall Quality Score:** `{overall_score} / 100.0` (Grade: **{grade}**)\n")

        md.append("## 📊 Executive Summary Table\n")
        md.append("| File | Quality Score | Issues Found | Refactoring Status |")
        md.append("| :--- | :---: | :---: | :--- |")

        for fr in file_results:
            status = "Refactored & Patched" if fr.diff != "No changes required." else "Clean / Compliant"
            md.append(f"| `{fr.filename}` | `{fr.quality_score}/100` | {len(fr.findings)} issues | {status} |")

        md.append("\n## 🐞 Detailed Diagnostic Findings & Diffs\n")
        for fr in file_results:
            md.append(f"### File: `{fr.filename}` (Score: {fr.quality_score}/100)\n")
            if not fr.findings:
                md.append("✓ *No code smells, performance bottlenecks, or security flaws detected.*\n")
            else:
                for f in fr.findings:
                    md.append(f"- **[{f.severity}] {f.category.upper()}** (Line {f.line}): {f.issue}")
                    md.append(f"  - *Recommendation:* {f.recommendation}")

            if fr.diff != "No changes required.":
                md.append("\n**Refactoring Diff:**")
                md.append("```diff")
                md.append(fr.diff)
                md.append("```\n")

        return "\n".join(md)


class AutonomousReviewEngine:
    """Master Code Review & Refactoring Engine."""

    def __init__(self):
        self.smell_scanner = CodeSmellScanner()
        self.perf_scanner = PerformanceScanner()
        self.security_scanner = SecurityScanner()
        self.refactorer = AutoRefactorer()
        self.diff_engine = DiffEngine()
        self.score_engine = QualityScoreEngine()
        self.report_producer = ReviewReportProducer()

    def review_and_refactor_file(self, filename: str, code: str) -> FileReviewResult:
        findings = []
        findings.extend(self.security_scanner.scan(filename, code))
        findings.extend(self.perf_scanner.scan(filename, code))
        findings.extend(self.smell_scanner.scan(filename, code))

        refactored_code = self.refactorer.refactor(filename, code, findings)
        diff = self.diff_engine.generate_diff(filename, code, refactored_code)
        score, grade, _ = self.score_engine.compute_score(findings)

        return FileReviewResult(
            filename=filename,
            original_code=code,
            refactored_code=refactored_code,
            diff=diff,
            findings=findings,
            quality_score=score
        )

    def review_project(self, files: Dict[str, str]) -> Dict[str, Any]:
        results: List[FileReviewResult] = []
        all_findings: List[DiagnosticFinding] = []

        for fname, code in files.items():
            fr = self.review_and_refactor_file(fname, code)
            results.append(fr)
            all_findings.extend(fr.findings)

        overall_score, grade, _ = self.score_engine.compute_score(all_findings)
        json_report = self.report_producer.produce_json(overall_score, grade, results)
        markdown_report = self.report_producer.produce_markdown(overall_score, grade, results)

        refactored_workspace = {
            fr.filename: fr.refactored_code for fr in results
        }

        return {
            "overall_quality_score": overall_score,
            "grade": grade,
            "file_results": results,
            "refactored_workspace": refactored_workspace,
            "json_report": json_report,
            "markdown_report": markdown_report
        }
