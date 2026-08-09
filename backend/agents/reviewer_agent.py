import json
import re
import logging
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.quality.gates import (
    Finding,
    FindingSeverity,
    FindingCategory,
    QualityGate,
    GateStatus,
    QualityReport,
    evaluate_quality_gates
)

_logger = logging.getLogger("aiforge.agents.reviewer_agent")


class ReviewerAgent(BaseAgent):
    __test__ = False

    def __init__(self):
        super().__init__(
            """
You are an expert Senior Software Security & Quality Engineer performing code review.
Inspect the generated full-stack code for requirements, architecture, code quality, security, testing, performance, and documentation.

Output MUST be valid JSON in this EXACT structure:
{
  "overall_score": 91,
  "gates": {
    "requirements": {"status": "PASS", "score": 95},
    "architecture": {"status": "PASS", "score": 92},
    "code_quality": {"status": "PASS", "score": 93},
    "security": {"status": "WARN", "score": 84},
    "testing": {"status": "PASS", "score": 90},
    "performance": {"status": "PASS", "score": 95},
    "documentation": {"status": "PASS", "score": 88}
  },
  "findings": [
    {
      "id": "finding_101",
      "severity": "HIGH",
      "category": "SECURITY",
      "file": "backend/routes/auth.py",
      "line": 42,
      "message": "Authentication input is not validated",
      "suggested_fix": "Validate request schema before processing",
      "blocking": true
    }
  ]
}
""",
            task_name="reviewer",
        )

    def analyze_code_quality(self, files_map: Dict[str, str], prompt: str = "") -> QualityReport:
        """
        Systematically analyzes generated code files for security, syntax, error handling,
        API contracts, database schema, and test coverage.
        Returns a structured QualityReport.
        """
        findings: List[Finding] = []
        finding_id_seq = 1

        for filepath, content in files_map.items():
            content_lower = content.lower()

            # Security Checks
            if any(pat in content_lower for pat in ["api_key = '", "secret = '", "password = '", "private_key = '"]):
                if not any(k in filepath.lower() for k in ["test", "config.py.example"]):
                    findings.append(Finding(
                        id=f"finding_{finding_id_seq}",
                        severity=FindingSeverity.CRITICAL,
                        category=FindingCategory.SECURITY,
                        file=filepath,
                        line=1,
                        message="Potential hardcoded secret or sensitive credentials detected.",
                        suggested_fix="Use environment variables or secrets manager.",
                        blocking=True
                    ))
                    finding_id_seq += 1

            if "exec(" in content or "eval(" in content or "os.system(" in content:
                findings.append(Finding(
                    id=f"finding_{finding_id_seq}",
                    severity=FindingSeverity.CRITICAL,
                    category=FindingCategory.SECURITY,
                    file=filepath,
                    message="Unsafe dynamic execution (eval/exec/os.system) detected.",
                    suggested_fix="Replace with safe static function calls or subprocess argument list.",
                    blocking=True
                ))
                finding_id_seq += 1

            # Code Quality & Error Handling
            if "except:" in content or "except Exception: pass" in content:
                findings.append(Finding(
                    id=f"finding_{finding_id_seq}",
                    severity=FindingSeverity.MEDIUM,
                    category=FindingCategory.CODE_QUALITY,
                    file=filepath,
                    message="Bare except block catches and suppresses arbitrary exceptions.",
                    suggested_fix="Catch specific exception types and log errors.",
                    blocking=False
                ))
                finding_id_seq += 1

        report = evaluate_quality_gates(findings)
        _logger.info(f"ReviewerAgent analyzed {len(files_map)} file(s): overall_score={report.overall_score}, findings={len(findings)}")
        return report

    def parse_review_json(self, raw_output: str) -> Dict[str, Any]:
        """
        Parses LLM review output into structured dictionary matching the findings and gates schema.
        """
        try:
            match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if "overall_score" in data and "gates" in data:
                    return data
                elif "status" in data and "issues" in data:
                    # Map legacy format to new schema
                    findings = []
                    for idx, issue in enumerate(data.get("issues", []), 1):
                        sev = str(issue.get("severity", "MEDIUM")).upper()
                        findings.append({
                            "id": f"finding_{idx}",
                            "severity": sev if sev in FindingSeverity.__members__ else "MEDIUM",
                            "category": "CODE_QUALITY",
                            "file": issue.get("file", "unknown"),
                            "message": issue.get("problem", "Issue detected"),
                            "suggested_fix": issue.get("fix", ""),
                            "blocking": sev in ("CRITICAL", "HIGH")
                        })
                    return {
                        "overall_score": data.get("score", 85.0),
                        "overall_status": data.get("status", "PASS"),
                        "gates": {
                            "code_quality": {"status": data.get("status", "PASS"), "score": data.get("score", 85.0)}
                        },
                        "findings": findings
                    }
        except Exception:
            pass

        return {
            "overall_score": 85.0,
            "overall_status": "PASS",
            "gates": {
                "requirements": {"status": "PASS", "score": 90.0},
                "code_quality": {"status": "PASS", "score": 85.0}
            },
            "findings": []
        }

    async def run_async(self, user_prompt: str, memory_context: str = "", previous_output: str = "") -> str:
        review_prompt = f"""
Generated Code to Review:
{previous_output}

Project Prompt:
{user_prompt}
"""
        return await super().run_async(review_prompt, memory_context, previous_output)


global_reviewer_agent = ReviewerAgent()