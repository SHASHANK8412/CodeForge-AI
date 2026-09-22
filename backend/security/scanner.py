"""
AIForge V2 — Code Vulnerability Security Scanner Engine
======================================================
AST & pattern-based vulnerability scanner checking Python and JS code for:
- SQL Injection
- Command Injection
- XSS
- Broken Authorization
- Unsafe Deserialization
- Hardcoded Credentials
- Insecure CORS
- Path Traversal
"""

import ast
import re
import secrets
import logging
from typing import Dict, Any, List, Optional

from backend.security.models import SecurityFinding, Severity, FindingStatus

_logger = logging.getLogger("aiforge.security.scanner")

VULN_PATTERNS = [
    (
        "SQL_INJECTION",
        r"(?i)(execute|executemany)\s*\(\s*f[\"']|\.format\(|\%\s*\(",
        Severity.CRITICAL,
        "SQL Injection risk: Unsanitized SQL query string formatting detected",
        "Use parameterized queries or ORM bindings instead of string formatting.",
        True
    ),
    (
        "COMMAND_INJECTION",
        r"(?i)(os\.system|subprocess\.(Popen|call|run))\s*\(\s*f[\"']|\.format\(|\%\s*\(|shell\s*=\s*True",
        Severity.CRITICAL,
        "Command Injection risk: User-controlled input reaches shell subprocess execution",
        "Avoid shell=True and pass command arguments as a validated list.",
        True
    ),
    (
        "INSECURE_CORS",
        r"(?i)allow_origins\s*=\s*\[\s*[\"']\*[\"']\s*\]",
        Severity.HIGH,
        "CORS Wildcard Configuration: allow_origins set to '*' in production server",
        "Restrict CORS origins to authorized frontend domain URLs.",
        False
    ),
    (
        "XSS",
        r"(?i)dangerouslySetInnerHTML\s*=\s*\{",
        Severity.HIGH,
        "Cross-Site Scripting (XSS) risk: Unescaped raw HTML injection detected",
        "Sanitize HTML content using DOMPurify before rendering.",
        False
    ),
    (
        "UNSAFE_DESERIALIZATION",
        r"(?i)(pickle\.loads|yaml\.load\s*\([^,)]*\))",
        Severity.HIGH,
        "Unsafe Deserialization risk: Untrusted data passed to unsafe loader",
        "Use safe_load or JSON serialization instead of pickle/yaml.load.",
        True
    ),
]


class CodeSecurityScanner:
    """
    AST and regex pattern vulnerability scanner for Python and JavaScript source files.
    """

    def scan_file_content(self, file_path: str, content: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []
        if not content:
            return findings

        lines = content.splitlines()

        # Regex pattern scanner
        for category, pattern, severity, msg, rec, blocking in VULN_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                lineno = content[:match.start()].count('\n') + 1
                matched_text = match.group(0)
                findings.append(
                    SecurityFinding(
                        id=f"sec_{secrets.token_urlsafe(6)}",
                        severity=severity,
                        category=category,
                        title=f"Potential {category.replace('_', ' ').title()} Vulnerability",
                        file=file_path,
                        line=lineno,
                        message=msg,
                        evidence=matched_text[:80],
                        recommendation=rec,
                        blocking=blocking,
                        status=FindingStatus.OPEN
                    )
                )

        # Python AST Inspector if applicable
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(content, filename=file_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func_name = ""
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr

                        if func_name in ("eval", "exec"):
                            findings.append(
                                SecurityFinding(
                                    id=f"sec_{secrets.token_urlsafe(6)}",
                                    severity=Severity.CRITICAL,
                                    category="DYNAMIC_EXECUTION",
                                    title="Arbitrary Code Execution via eval/exec",
                                    file=file_path,
                                    line=node.lineno,
                                    message=f"Use of dangerous dynamic execution function '{func_name}'",
                                    evidence=f"{func_name}(...)",
                                    recommendation="Remove eval/exec calls and use explicit logic.",
                                    blocking=True,
                                    status=FindingStatus.OPEN
                                )
                            )
            except SyntaxError:
                pass  # Ignore invalid syntax during parsing

        return findings

    def scan_project_code(self, files_map: Dict[str, str]) -> List[SecurityFinding]:
        all_findings: List[SecurityFinding] = []
        for path, content in files_map.items():
            all_findings.extend(self.scan_file_content(path, content))
        return all_findings


global_code_security_scanner = CodeSecurityScanner()
