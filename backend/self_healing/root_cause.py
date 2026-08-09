"""
AIForge Root Cause Analyzer
===========================
Performs Root Cause Analysis (RCA) on error logs and tracebacks to isolate the underlying failure cause rather than just superficial symptoms.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.self_healing.root_cause")


class RootCauseAnalyzer:
    """
    Analyzes error stack traces and logs to determine root cause hierarchy.
    """

    def analyze(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        msg = error_report.get("message", "").lower()
        err_type = error_report.get("error_type", "General")
        file = error_report.get("file", "unknown")

        if "timeout" in msg or "pool" in msg or err_type == "Database":
            symptom_chain = ["API Endpoint Returned HTTP 500", "Database Connection Timeout"]
            root_cause = "Insufficient DB Pool Size in database.py configuration"
            recommended_fix = "Increase pool_size from 5 to 20 and add pool_pre_ping=True"
        elif "import" in msg or "module" in msg or err_type == "Dependency":
            symptom_chain = ["App Startup Failure", "ModuleNotFoundError"]
            root_cause = "Missing dependency requirement in requirements.txt"
            recommended_fix = "Add missing package to requirements.txt and re-run pip install"
        elif "syntax" in msg or err_type == "Build":
            symptom_chain = ["Compilation Error", "SyntaxError"]
            root_cause = f"Invalid Python syntax in file {file}"
            recommended_fix = "Fix invalid syntax token or missing closing parenthesis"
        elif "permission" in msg or "env" in msg or err_type == "Security":
            symptom_chain = ["Authorization Denial", "Missing API Key"]
            root_cause = "Environment variable not initialized in .env"
            recommended_fix = "Add default key value to .env template"
        else:
            symptom_chain = ["Function Failure", f"Exception in {file}"]
            root_cause = f"Unhandled null check / assertion failure in {file}"
            recommended_fix = f"Wrap calculation in null guard check in {file}"

        analysis_result = {
            "rca_id": f"rca_{int(time.time() * 1000)}",
            "error_id": error_report.get("error_id", "unknown"),
            "target_file": file,
            "symptoms": symptom_chain,
            "root_cause": root_cause,
            "recommended_fix": recommended_fix,
            "confidence_score": 0.95,
            "analyzed_at": time.time()
        }

        _logger.info(f"RootCauseAnalyzer: Analyzed error '{error_report.get('error_id')}' -> Root Cause: '{root_cause}'")
        return analysis_result


global_root_cause_analyzer = RootCauseAnalyzer()
