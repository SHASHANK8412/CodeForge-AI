import json
import logging
from typing import Dict, Any, List
from backend.services.llm import generate_text

_logger = logging.getLogger("aiforge.sre")

class RootCauseAnalyzer:
    """
    Invokes LLM analysis to trace diagnostic reports, returning structured JSON containing
    the root cause, severity, recommended recovery actions, and confidence score.
    """

    def __init__(self, model_name: str = "qwen2.5-coder:latest") -> None:
        self.model_name = model_name

    def analyze(
        self,
        incidents: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        health: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submits incident alerts and metrics snapshots to the LLM and returns a parsed JSON diagnosis.
        """
        _logger.info("Executing SRE Root Cause Analysis Agent...")

        if not incidents:
            return {
                "incident": "None",
                "severity": "Info",
                "service": "All Systems Operational",
                "root_cause": "No active threshold violations discovered.",
                "affected_components": [],
                "confidence": 1.0,
                "recommended_action": "None"
            }

        # Format system snapshot for the LLM
        prompt = f"""
System Diagnostics Snapshot:
- Active Incidents: {json.dumps(incidents, indent=2)}
- Metrics State: {json.dumps(metrics, indent=2)}
- Health Check Scores: {json.dumps(health, indent=2)}

You are an SRE Agent. Analyze the operational failure above and output a structured JSON response identifying the primary failure, root cause, confidence score (0.0 to 1.0), and the recommended recovery action.

Your response must be a valid JSON object matching this schema exactly (do not output any other conversational prefix/suffix text, only the raw JSON structure):
{{
    "incident": "Database Connection Failure",
    "severity": "Critical",
    "service": "Backend API",
    "root_cause": "PostgreSQL unavailable",
    "affected_components": ["API", "Authentication"],
    "confidence": 0.96,
    "recommended_action": "Restart Database"
}}
"""
        system_prompt = "You are an AI-SRE expert site reliability agent. Always output valid raw JSON data."

        try:
            raw_response = generate_text(
                system_prompt=system_prompt,
                prompt=prompt,
                model=self.model_name,
                task="general"
            )

            # Strip markdown fences if outputted by the model
            clean_res = raw_response.strip()
            if clean_res.startswith("```"):
                # extract from fences
                lines = clean_res.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_res = "\n".join(lines).strip()

            parsed = json.loads(clean_res)
            
            # Basic validation
            required_keys = ["incident", "severity", "service", "root_cause", "affected_components", "confidence", "recommended_action"]
            for k in required_keys:
                if k not in parsed:
                    # Fallback default value if key is missing
                    if k == "affected_components":
                        parsed[k] = []
                    elif k == "confidence":
                        parsed[k] = 0.5
                    else:
                        parsed[k] = "Unknown"
            
            _logger.info(f"SRE Root Cause successfully analyzed: {parsed.get('root_cause')}")
            return parsed

        except Exception as e:
            _logger.error(f"Failed to compile root cause analysis JSON: {str(e)}")
            # Robust fallback logic
            primary_incident = incidents[0]
            return {
                "incident": primary_incident.get("signature", "System Incident"),
                "severity": primary_incident.get("severity", "Critical"),
                "service": primary_incident.get("service", "Unknown"),
                "root_cause": primary_incident.get("description", "Unknown system threshold violation"),
                "affected_components": [primary_incident.get("service", "API")],
                "confidence": 0.60,
                "recommended_action": self._map_fallback_action(primary_incident.get("signature", ""))
            }

    def _map_fallback_action(self, signature: str) -> str:
        sig_lower = signature.lower()
        if "db" in sig_lower or "postgres" in sig_lower:
            return "Restart Database"
        elif "redis" in sig_lower:
            return "Clear Cache"
        elif "ollama" in sig_lower:
            return "Restart LLM Instance"
        elif "cpu" in sig_lower or "memory" in sig_lower:
            return "Scale Replicas"
        elif "api" in sig_lower:
            return "Restart Container"
        return "Restart Container"
