import re
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.evolution")

class SecurityInspector:
    """
    Scans python and javascript workspace files for vulnerabilities (hardcoded secrets, open CORS).
    """

    def __init__(self) -> None:
        pass

    def run_security_scan(self, workspace_path: str) -> List[Dict[str, Any]]:
        """
        Parses python files looking for security vulnerabilities.
        """
        root = Path(workspace_path)
        findings: List[Dict[str, Any]] = []

        # Secret patterns scanner regex
        secret_pattern = re.compile(r'(api_key|secret|password|token)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']', re.IGNORECASE)
        # Open CORS check regex
        cors_pattern = re.compile(r'allow_origins\s*=\s*\[\s*["\']\*["\']\s*\]')
        # SQL Injection check regex
        sql_inject_pattern = re.compile(r'\.execute\(\s*f["\']')

        for file_path in root.glob("backend/**/*.py"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    # 1. Hardcoded Secret Check
                    if secret_pattern.search(line) and not "env" in line.lower() and not "default" in line.lower():
                        findings.append({
                            "file": str(file_path.relative_to(root)),
                            "line": idx + 1,
                            "vulnerability": "Hardcoded Secret",
                            "description": "Potential hardcoded credential or API secret token key discovered.",
                            "severity": "High",
                            "proposed_fix": "Extract API key to environment variables (.env file)."
                        })

                    # 2. Open CORS policy check
                    if cors_pattern.search(line):
                        findings.append({
                            "file": str(file_path.relative_to(root)),
                            "line": idx + 1,
                            "vulnerability": "Permissive CORS Configuration",
                            "description": "CORS allow_origins is set to wildcard '*' in FastAPI middleware configuration.",
                            "severity": "Medium",
                            "proposed_fix": "Replace '*' with a list of explicit trusted domain origins."
                        })

                    # 3. SQL Injection check
                    if sql_inject_pattern.search(line):
                        findings.append({
                            "file": str(file_path.relative_to(root)),
                            "line": idx + 1,
                            "vulnerability": "Potential SQL Injection",
                            "description": "Executing raw SQL statement using string interpolation instead of parameterized placeholders.",
                            "severity": "Critical",
                            "proposed_fix": "Use db binding parameters query templates: execute('SELECT * FROM users WHERE id = %s', (user_id,))."
                        })
            except Exception as e:
                _logger.error(f"Skipping security audit on file {file_path.name}: {str(e)}")

        return findings
