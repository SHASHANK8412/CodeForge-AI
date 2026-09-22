"""
AIForge Autonomous Engineering Platform — DiagnosticAgent
==========================================================
Analyzes execution failures, stack traces, stderr, and source files using
Ollama JSON-schema structured outputs to determine root cause, affected files,
severity, confidence, recommended fix, and verification commands.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.agents.base_agent import BaseAgent
from backend.models.model_router import global_model_router
from backend.execution.error_classifier import global_error_classifier

_logger = logging.getLogger("aiforge.agents.diagnostic_agent")


class DiagnosticResult(BaseModel):
    root_cause: str = ""
    error_category: str = "unknown_error"
    affected_files: List[str] = Field(default_factory=list)
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    confidence: float = 0.90
    recommended_fix: str = ""
    verification_command: str = ""


class DiagnosticAgent(BaseAgent):
    """
    Dedicated Diagnostic Agent utilizing Ollama JSON Schema structured outputs.
    """

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Diagnostic Agent for AIForge. Your job is to analyze build, "
                "compilation, runtime, and test execution failures. Identify the exact root cause, "
                "which files and line numbers caused the failure, and formulate the minimal targeted fix. "
                "You MUST return valid JSON adhering strictly to the requested schema."
            ),
            task_name="diagnostic"
        )

    def diagnose_failure(
        self,
        execution_report: Dict[str, Any],
        files_manifest: Dict[str, str],
        architecture_spec: Optional[Dict[str, Any]] = None,
        previous_fixes: Optional[List[Dict[str, Any]]] = None
    ) -> DiagnosticResult:
        stdout = str(execution_report.get("stdout", ""))
        stderr = str(execution_report.get("stderr", ""))
        error_msg = str(execution_report.get("error_message", ""))
        failed_cmd = str(execution_report.get("failed_command", ""))

        # 1. Deterministic error classification
        classified_category = global_error_classifier.classify(stderr or error_msg or stdout)

        # 2. Extract potential file references from stack traces deterministically
        affected_files = []
        for path in files_manifest.keys():
            base_name = path.split("/")[-1]
            if base_name in stderr or path in stderr or base_name in error_msg:
                affected_files.append(path)

        if not affected_files and files_manifest:
            affected_files = [list(files_manifest.keys())[0]]

        # Construct prompt for LLM reasoning
        prompt_text = (
            f"Execution Failed!\n"
            f"Failed Command: {failed_cmd}\n"
            f"Error Message: {error_msg[:1000]}\n"
            f"Stderr:\n{stderr[:1500]}\n\n"
            f"Available Files: {list(files_manifest.keys())}\n"
            f"Identified Affected Files: {affected_files}\n\n"
            f"Provide a structured JSON diagnosis with keys: root_cause, error_category, affected_files, severity, confidence, recommended_fix, verification_command."
        )

        try:
            raw_response = self.generate(prompt_text)
            clean_json = raw_response
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            data = json.loads(clean_json)


            return DiagnosticResult(
                root_cause=data.get("root_cause") or f"Execution failure in command '{failed_cmd}'",
                error_category=data.get("error_category") or classified_category,
                affected_files=data.get("affected_files") or affected_files,
                severity=data.get("severity", "HIGH"),
                confidence=float(data.get("confidence", 0.90)),
                recommended_fix=data.get("recommended_fix") or "Apply minimal syntax and dependency correction.",
                verification_command=data.get("verification_command") or failed_cmd
            )
        except Exception as exc:
            _logger.warning(f"[DiagnosticAgent] Structured LLM diagnosis fallback triggered: {exc}")
            return DiagnosticResult(
                root_cause=f"Failure in '{failed_cmd}': {error_msg[:200] or 'Runtime Error'}",
                error_category=classified_category,
                affected_files=affected_files,
                severity="HIGH",
                confidence=0.85,
                recommended_fix="Update syntax and imports in affected file.",
                verification_command=failed_cmd
            )


global_diagnostic_agent = DiagnosticAgent()
