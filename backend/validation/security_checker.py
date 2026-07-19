import re
import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

# Regex rules for security threats
RULES = [
    {
        "name": "Hardcoded Secret",
        "pattern": r"\b(password|secret|api_key|token|passwd|private_key)\s*=\s*['\"]([^'\"]{8,})['\"]",
        "severity": "critical",
        "recommendation": "Use environment variables or secrets manager instead of hardcoding values"
    },
    {
        "name": "SQL Injection Risk",
        "pattern": r"\.execute\(\s*f['\"][^'\"]*\{\w+\}[^'\"]*['\"]",
        "severity": "critical",
        "recommendation": "Use parameterized queries/prepared statements instead of string formatting"
    },
    {
        "name": "Command Injection Risk",
        "pattern": r"\bsubprocess\.(?:run|call|Popen)\([^)]*shell\s*=\s*True",
        "severity": "high",
        "recommendation": "Avoid using shell=True, pass arguments as a list to execute commands directly"
    },
    {
        "name": "Unsafe Execution API",
        "pattern": r"\b(eval|exec)\s*\(",
        "severity": "high",
        "recommendation": "Avoid eval() and exec() as they permit arbitrary expression evaluation and code injection"
    },
    {
        "name": "Weak JWT Configuration",
        "pattern": r"\bjwt\.encode\([^)]*algorithm\s*=\s*['\"]none['\"]",
        "severity": "critical",
        "recommendation": "Do not use 'none' algorithm for JWT; sign with HS256, RS256, or ES256 instead"
    },
    {
        "name": "Unsafe CORS Wildcard",
        "pattern": r"\ballow_origins\s*=\s*\[\s*['\"]\*['\"]",
        "severity": "medium",
        "recommendation": "Specify explicit origins instead of wildcard '*' in production configurations"
    },
    {
        "name": "Directory Traversal / Unsafe Uploads",
        "pattern": r"\bsend_from_directory\([^)]*path\s*=\s*\w+",
        "severity": "high",
        "recommendation": "Sanitize user paths with secure_filename before serving files or writing to directories"
    }
]

class SecurityChecker:
    """
    Validates codebase against common security threats: hardcoded credentials, command injection, 
    SQL injection, unsafe eval/exec, insecure CORS, and weak token signing.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Security Checker Started")

        errors = []
        warnings = []
        issues_meta = [] # structured issues details: {name, file, line, severity, recommendation}
        files_checked = 0

        # Scan all text-based files
        extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".sql", ".env", ".yml", ".yaml"]
        project_files = list(get_all_files(project_path, extensions))
        
        for file_path in project_files:
            files_checked += 1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check each rule
                for rule in RULES:
                    matches = re.finditer(rule["pattern"], content, re.IGNORECASE if rule["name"] != "SQL Injection Risk" else 0)
                    for m in matches:
                        # Find line number
                        line_no = content[:m.start()].count("\n") + 1
                        issue_msg = f"{rule['name']} detected in {file_path.name} at line {line_no}"
                        
                        issue_detail = {
                            "name": rule["name"],
                            "file": str(file_path.relative_to(project_path)),
                            "line": line_no,
                            "severity": rule["severity"],
                            "recommendation": rule["recommendation"]
                        }
                        issues_meta.append(issue_detail)
                        
                        if rule["severity"] in {"critical", "high"}:
                            errors.append(issue_msg)
                        else:
                            warnings.append(issue_msg)
            except Exception as exc:
                warnings.append(f"Could not open file {file_path.name} for security audit: {exc}")

        execution_time = round(time.perf_counter() - start_time, 4)
        
        # Deduct score based on issues
        score = 100.0
        for issue in issues_meta:
            if issue["severity"] == "critical":
                score -= 20
            elif issue["severity"] == "high":
                score -= 10
            elif issue["severity"] == "medium":
                score -= 5
                
        score = max(0.0, min(100.0, score))
        status = "PASS" if score >= 90.0 else "FAIL"

        _logger.info(f"Security Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Security Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "files_scanned": files_checked,
                "issues": issues_meta
            }
        )
