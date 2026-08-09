"""
AIForge Error Analyzer Agent
============================
Reads build logs, runtime logs, and stack traces to analyze and categorize project errors into structured JSON representations.
"""

import json
import logging
import time
from typing import Dict, Any, Union
from backend.utils.log_parser import global_log_parser

_logger = logging.getLogger("aiforge.agents.error_analyzer")


class ErrorAnalyzerAgent:
    """
    Agent responsible for ingesting system error logs, runtime exceptions, and build output to produce structured error diagnostics.
    """

    def analyze_log(self, log_input: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingests log text or dict, categorizes error, and outputs structured JSON diagnostic report.
        """
        if isinstance(log_input, dict):
            raw_text = log_input.get("stack_trace") or log_input.get("message") or log_input.get("log") or str(log_input)
        else:
            raw_text = str(log_input)

        parsed = global_log_parser.parse_log(raw_text)

        # Merge with dict metadata if provided
        if isinstance(log_input, dict):
            if "file" in log_input and log_input["file"] != "unknown":
                parsed["file"] = log_input["file"]
            if "line" in log_input and log_input["line"] > 0:
                parsed["line"] = log_input["line"]
            if "severity" in log_input:
                parsed["severity"] = log_input["severity"]

        analysis = {
            "error_id": f"err_an_{int(time.time() * 1000)}",
            "error_type": parsed.get("error_type", "UnknownError"),
            "severity": parsed.get("severity", "Medium"),
            "file": parsed.get("file", "unknown"),
            "line": parsed.get("line", 1),
            "cause": parsed.get("cause", "Unspecified runtime failure"),
            "category": parsed.get("category", "General"),
            "raw_traceback": parsed.get("raw_traceback", raw_text),
            "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        _logger.info(f"ErrorAnalyzerAgent: Categorized [{analysis['category']}:{analysis['error_type']}] in {analysis['file']}:L{analysis['line']}")
        return analysis

    def analyze_to_json(self, log_input: Union[str, Dict[str, Any]]) -> str:
        """
        Returns structured JSON string as required by agent specification.
        """
        data = self.analyze_log(log_input)
        return json.dumps(data, indent=2)


global_error_analyzer = ErrorAnalyzerAgent()
