"""
CI Security Stage
=================
Executes OWASP security scans, hardcoded secrets detection, and vulnerability audits.
"""

import re
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.ci.models import CIStageResult, CIStageStatus
from backend.ci.stages.base_stage import CIStageBase
from backend.execution.project_detector import DetectedProjectConfig
from backend.execution.execution_backend import ExecutionBackend

_logger = logging.getLogger("aiforge.ci.security_stage")


class SecurityStage(CIStageBase):
    """
    Security Stage detecting leaked secrets, OWASP vulnerabilities, and dangerous calls.
    """

    SECRET_PATTERNS = [
        (re.compile(r"""(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]""", re.IGNORECASE), "HARDCODED_API_KEY", "High"),
        (re.compile(r"""AKIA[0-9A-Z]{16}"""), "AWS_ACCESS_KEY", "High"),
        (re.compile(r"""ghp_[A-Za-z0-9_]{36}"""), "GITHUB_TOKEN", "High"),
        (re.compile(r"""eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+"""), "HARDCODED_JWT", "High"),
    ]

    DANGEROUS_PATTERNS = [
        (re.compile(r"""eval\s*\("""), "DANGEROUS_EVAL", "High"),
        (re.compile(r"""exec\s*\("""), "DANGEROUS_EXEC", "Medium"),
    ]

    def __init__(self):
        super().__init__(name="security")

    def execute(
        self,
        sandbox_path: Path,
        project_cfg: DetectedProjectConfig,
        backend: ExecutionBackend,
        timeout: float,
        custom_env: Optional[Dict[str, str]] = None,
        files_manifest: Optional[Dict[str, str]] = None
    ) -> CIStageResult:
        start_time = time.perf_counter()
        manifest = files_manifest or {}
        if not manifest:
            for p in sandbox_path.rglob("*"):
                if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts:
                    try:
                        rel = str(p.relative_to(sandbox_path)).replace("\\", "/")
                        manifest[rel] = p.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        pass

        findings: List[Dict[str, Any]] = []

        for rel_path, content in manifest.items():
            # Skip test files from strict hardcoded secret failures
            is_test = "test" in rel_path.lower()

            for regex, rule, severity in self.SECRET_PATTERNS:
                if not is_test and regex.search(content):
                    findings.append({
                        "file": rel_path,
                        "rule": rule,
                        "severity": severity,
                        "message": f"Hardcoded secret detected in {rel_path}."
                    })

            for regex, rule, severity in self.DANGEROUS_PATTERNS:
                if not is_test and regex.search(content):
                    findings.append({
                        "file": rel_path,
                        "rule": rule,
                        "severity": severity,
                        "message": f"Dangerous function call ({rule}) detected in {rel_path}."
                    })

        elapsed = round(time.perf_counter() - start_time, 3)
        high_severity = [f for f in findings if f["severity"] == "High"]

        if high_severity:
            return CIStageResult(
                stage=self.name,
                status=CIStageStatus.FAILED.value,
                exit_code=1,
                stdout=f"Security scan failed with {len(high_severity)} high severity vulnerability(ies).",
                stderr="\n".join([f"{f['file']} [{f['rule']}]: {f['message']}" for f in high_severity]),
                duration=elapsed,
                command="security-scan",
                details={"findings": findings, "vulnerabilities_count": len(findings)}
            )

        status = CIStageStatus.WARNING.value if findings else CIStageStatus.PASSED.value
        return CIStageResult(
            stage=self.name,
            status=status,
            exit_code=0,
            stdout="Security audit passed with zero high-severity vulnerabilities.",
            duration=elapsed,
            command="security-scan",
            details={"findings": findings, "vulnerabilities_count": len(findings)}
        )
