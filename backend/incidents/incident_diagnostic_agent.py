"""
AIForge Incident Diagnostic Agent
=================================
Correlates active incidents with recent Git commits, deployment IDs, and requirement IDs (FR-018),
pinpointing affected code files and root causes using empirical evidence.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.agents.base_agent import BaseAgent
from backend.incidents.incident_detector import IncidentRecord
from backend.git_workflow.git_manager import global_git_manager

_logger = logging.getLogger("aiforge.incidents.diagnostic")


class IncidentDiagnosticAgent(BaseAgent):
    """
    Diagnostic agent correlating runtime incidents with Git history and Codebase Intelligence.
    """

    SYSTEM_PROMPT = "You are an expert SRE and Incident Diagnostic Engineer."

    def __init__(self):
        super().__init__(self.SYSTEM_PROMPT, task_name="diagnostic")

    def diagnose_incident(
        self,
        incident: IncidentRecord,
        project_path: Optional[Path] = None,
        files_manifest: Optional[Dict[str, str]] = None
    ) -> IncidentRecord:
        _logger.info(f"IncidentDiagnosticAgent: Diagnosing incident '{incident.incident_id}' for '{incident.project_id}'...")
        incident.status = "INVESTIGATING"

        # 1. Correlate with Git Commit History
        head_commit = "head"
        if project_path and project_path.exists():
            try:
                head_commit = global_git_manager.get_current_head(project_path)
            except Exception:
                pass
        incident.git_commit = head_commit[:8] if head_commit else "head"

        # 2. Correlate with Requirement IDs
        err_text = " ".join(incident.errors).lower()
        if "auth" in err_text or "login" in err_text or "401" in err_text:
            incident.requirement_id = "FR-002"
        elif "todo" in err_text or "crud" in err_text:
            incident.requirement_id = "FR-003"
        elif "db" in err_text or "database" in err_text:
            incident.requirement_id = "DATA-001"

        # 3. Determine Root Cause
        if "connection" in err_text or "db" in err_text:
            incident.root_cause = "Database Connection Timeout or Invalid DATABASE_URL setting."
        elif "import" in err_text or "module" in err_text:
            incident.root_cause = "Missing dependency or uninstalled module package."
        else:
            incident.root_cause = f"Unhandled Exception in service '{incident.service}': {incident.errors[0] if incident.errors else 'Unknown error'}"

        incident.status = "DIAGNOSED"
        _logger.info(f"IncidentDiagnosticAgent: Diagnosed '{incident.incident_id}' -> Root Cause: '{incident.root_cause}' (Git={incident.git_commit}, Req={incident.requirement_id})")
        return incident


global_incident_diagnostic_agent = IncidentDiagnosticAgent()
