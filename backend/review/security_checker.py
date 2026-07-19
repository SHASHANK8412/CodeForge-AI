import re
import logging
from pathlib import Path

_logger = logging.getLogger("aiforge.performance")


class SecurityChecker:
    """
    Performs static security analysis on code files to identify vulnerabilities like
    SQL injection, command injection, hardcoded secrets, unsafe deserialization,
    plaintext passwords, and weak cryptography configurations.
    """

    def __init__(self) -> None:
        pass

    def check_project(self, project_path: Path) -> list[dict]:
        """
        Scans all files inside project_path for common security vulnerabilities.
        """
        _logger.info("INFO Starting security checking...")
        findings = []

        all_files = list(project_path.glob("**/*.py")) + \
                    list(project_path.glob("**/*.js")) + \
                    list(project_path.glob("**/*.jsx"))

        for file_path in all_files:
            try:
                rel_file = str(file_path.relative_to(project_path))
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                content = "".join(lines)

                # 1. Check Hardcoded Secrets
                # Matches: SECRET_KEY = "xyz" or api_key = "12345" where string length is >= 12 and contains characters
                for line_no, line in enumerate(lines, 1):
                    secret_match = re.search(
                        r"(?i)\b(?:secret|api_key|token|password|passwd|private_key)\b\s*=\s*['\"]([^'\"]{10,})['\"]",
                        line
                    )
                    # Exclude typical placeholder words or env lookups
                    if secret_match:
                        val = secret_match.group(1)
                        if not any(placeholder in val.lower() for placeholder in ["placeholder", "env", "config", "your_", "secure_"]):
                            findings.append({
                                "severity": "critical",
                                "file": rel_file,
                                "line": line_no,
                                "issue": f"Possible hardcoded secret or token detected: '{secret_match.group(0).strip()}'",
                                "recommendation": "Move secrets to environment variables and load them via os.getenv()"
                            })

                # 2. Check SQL Injection (Concatenating / Interpolating raw query strings)
                for line_no, line in enumerate(lines, 1):
                    # Check for f-string sql calls or string addition in sql queries
                    sql_match = re.search(
                        r"(?i)\b(?:execute|query|select|insert|update|delete)\b.*\b(?:f['\"].*\{|\+.*['\"])",
                        line
                    )
                    if sql_match:
                        findings.append({
                            "severity": "critical",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Potential SQL Injection vulnerability due to string concatenation or interpolation in SQL query",
                            "recommendation": "Use parameterized queries or ORM placeholders instead of string manipulation"
                        })

                # 3. Check Command Injection (shell=True or os.system)
                for line_no, line in enumerate(lines, 1):
                    if "shell=True" in line and "subprocess" in line:
                        findings.append({
                            "severity": "critical",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Unsafe subprocess execution with shell=True detected",
                            "recommendation": "Execute commands as lists without shell=True, or sanitize arguments thoroughly"
                        })
                    if "os.system(" in line:
                        findings.append({
                            "severity": "critical",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Unsafe os.system call detected",
                            "recommendation": "Use subprocess.run() with list-based arguments to prevent shell expansion"
                        })

                # 4. Check Insecure Deserialization (pickle or yaml.unsafe_load)
                for line_no, line in enumerate(lines, 1):
                    if "pickle.loads(" in line or "pickle.load(" in line:
                        findings.append({
                            "severity": "critical",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Insecure deserialization using pickle detected",
                            "recommendation": "Use secure formats like JSON, MessagePack, or Protocol Buffers"
                        })
                    if "yaml.unsafe_load(" in line:
                        findings.append({
                            "severity": "critical",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Insecure YAML loading using unsafe_load detected",
                            "recommendation": "Use yaml.safe_load() to prevent arbitrary code execution"
                        })

                # 5. Check Plaintext Passwords / Weak Hashing
                for line_no, line in enumerate(lines, 1):
                    if re.search(r"(?i)\bmd5\b|\bsha1\b", line) and ("hash" in line.lower() or "crypt" in line.lower()):
                        # Check if md5 or sha1 is being used for password hashing
                        findings.append({
                            "severity": "warning",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Weak cryptographic hashing algorithm (MD5/SHA1) detected",
                            "recommendation": "Use secure hashing algorithms like bcrypt, Argon2, or PBKDF2"
                        })

                # 6. Check React dangerouslySetInnerHTML
                for line_no, line in enumerate(lines, 1):
                    if "dangerouslySetInnerHTML" in line:
                        findings.append({
                            "severity": "warning",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "React dangerouslySetInnerHTML detected",
                            "recommendation": "Ensure input values are completely sanitized using DOMPurify before rendering"
                        })

                # 7. Check Unsafe Path Traversals
                for line_no, line in enumerate(lines, 1):
                    if re.search(r"open\(.*(?:\+|,)\s*(?:request|params|user_input|filename|file_name)", line):
                        findings.append({
                            "severity": "warning",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Potential path traversal vulnerability during file open operation",
                            "recommendation": "Use Path.resolve() or sanitize file paths using safe path utilities"
                        })

            except Exception as exc:
                _logger.warning(f"Failed to scan security issues for {file_path}: {exc}")

        _logger.info("INFO Security checking completed")
        return findings
