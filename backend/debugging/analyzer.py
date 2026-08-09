import re
import logging
from typing import Dict, Any, List

from backend.debugging.error_classifier import global_error_classifier

logger = logging.getLogger("aiforge.debugging.analyzer")


class DebugAnalyzer:
    """
    DebugAnalyzer parses stack traces and execution logs, pinpointing error files,
    line numbers, and generating classified diagnostic reports.
    """

    def analyze_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        classified = []

        for err in errors:
            filepath = err.get("file", "")
            err_type = err.get("error", "RuntimeError")
            msg = err.get("stderr", err.get("message", ""))

            diag = global_error_classifier.classify_error(err_type, msg, filepath)
            classified.append(diag)

        logger.info(f"DebugAnalyzer diagnosed {len(classified)} errors.")
        return {
            "diagnostics_count": len(classified),
            "diagnostics": classified
        }


# Global DebugAnalyzer Instance
global_debug_analyzer = DebugAnalyzer()
