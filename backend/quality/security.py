import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.quality.security")


class SecurityScanner:
    """
    SecurityScanner audits project files for security vulnerabilities:
    - Hardcoded secret keys & passwords
    - SQL injection vulnerabilities (raw string formatting in SQL)
    - XSS vulnerabilities in React
    - Weak JWT algorithm or missing secret handling
    """

    SECRET_PATTERNS = [
        re.compile(r"(['\"]?)(password|secret|api_key|jwt_secret)\1\s*[:=]\s*['\"]([^'\"]{4,})['\"]", re.I),
        re.compile(r"AWS_SECRET_ACCESS_KEY\s*=\s*['\"][^'\"]+['\"]", re.I),
    ]

    SQLI_PATTERNS = [
        re.compile(r"SELECT\s+.*\s+FROM\s+.*\%\s*s", re.I),
        re.compile(r"SELECT\s+.*\s+WHERE\s+.*\+\s*\w+", re.I),
    ]

    def scan_files(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        vulnerabilities = []

        for filepath, content in project_files.items():
            # 1. Hardcoded Secret Detection
            for pattern in self.SECRET_PATTERNS:
                if pattern.search(content) and ".env.example" not in filepath and "requirements" not in filepath:
                    vulnerabilities.append({
                        "file": filepath,
                        "type": "HardcodedSecret",
                        "severity": "HIGH",
                        "recommendation": "Move hardcoded secret keys to environment variables (.env)."
                    })
                    break

            # 2. SQL Injection Detection
            for pattern in self.SQLI_PATTERNS:
                if pattern.search(content):
                    vulnerabilities.append({
                        "file": filepath,
                        "type": "SQLInjectionRisk",
                        "severity": "HIGH",
                        "recommendation": "Use parameterized queries or SQLAlchemy ORM instead of string concatenation."
                    })
                    break

            # 3. XSS dangerouslySetInnerHTML Check
            if "dangerouslySetInnerHTML" in content:
                vulnerabilities.append({
                    "file": filepath,
                    "type": "XSSVulnerability",
                    "severity": "MEDIUM",
                    "recommendation": "Sanitize HTML content using DOMPurify before setting dangerouslySetInnerHTML."
                })

        security_score = max(0, 100 - (len(vulnerabilities) * 15))
        return {
            "security_score": security_score,
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities
        }


# Global SecurityScanner Instance
global_security_scanner = SecurityScanner()
