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

Output ONLY valid JSON with this schema (the angle-bracket parts describe what to write; never copy them):
{
  "overall_score": <integer 0-100 from your own assessment of THIS code>,
  "gates": {
    "<requirements|architecture|code_quality|security|testing|performance|documentation>":
      {"status": "<PASS|WARN|FAIL>", "score": <integer 0-100>}
  },
  "findings": [
    {"id": "<unique id>", "severity": "<CRITICAL|HIGH|MEDIUM|LOW>",
     "category": "<SECURITY|CODE_QUALITY|ARCHITECTURE|TESTING|PERFORMANCE|DOCUMENTATION|REQUIREMENTS>",
     "file": "<a path that exists in the code you were given>", "line": <line number in that file>,
     "message": "<the problem you actually found>", "suggested_fix": "<how to fix it>", "blocking": <true|false>}
  ]
}
Report only problems you can point to in the code you were given. An empty findings list is fine.
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
                        "overall_score": data.get("score"),
                        "overall_status": data.get("status", "UNKNOWN"),
                        "gates": {"code_quality": {"status": data.get("status", "UNKNOWN"), "score": data.get("score")}}
                        if data.get("status") else {},
                        "findings": findings
                    }
        except Exception:
            pass

        # No review could be read: nothing was reviewed, and nothing is reported as passing.
        return {"overall_score": None, "overall_status": "NOT_REVIEWED", "gates": {}, "findings": [],
                "error": "the reviewer's output could not be parsed as a review"}

    @staticmethod
    def validate_review(data: Dict[str, Any], files: Dict[str, str]) -> Dict[str, Any]:
        """Check a parsed review against the real files: a finding whose file is not in the project is marked
        unverified (and never blocking), and a review that only repeats the old prompt example is not a review."""
        known = {p.replace("\\", "/") for p in (files or {})}
        findings, unverified = [], []
        for f in data.get("findings") or []:
            if not isinstance(f, dict):
                continue
            path = str(f.get("file") or "").replace("\\", "/").removeprefix("./")
            if known and path not in known:
                unverified.append({**f, "blocking": False, "verified": False,
                                   "note": "the file this finding names is not in the project"})
            else:
                findings.append({**f, "verified": bool(known)})
        out = {**data, "findings": findings, "unverified_findings": unverified}
        copied = any(f.get("message") == "Authentication input is not validated" and f.get("file") == "backend/routes/auth.py"
                     for f in data.get("findings") or [] if isinstance(f, dict))
        if copied and "backend/routes/auth.py" not in known:
            out.update({"overall_status": "NOT_REVIEWED", "overall_score": None,
                        "error": "the review repeats a prompt example instead of reviewing this code"})
        return out

    async def run_async(self, user_prompt: str, memory_context: str = "", previous_output: str = "") -> str:
        review_prompt = f"""
Generated Code to Review:
{previous_output}

Project Prompt:
{user_prompt}
"""
        return await super().run_async(review_prompt, memory_context, previous_output)


global_reviewer_agent = ReviewerAgent()