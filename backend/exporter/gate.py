"""
AIForge Centralized Single Authoritative Export Gate (Phase 11)
==============================================================
Validates that project state and verification evidence strictly satisfy
all security, execution, test pass, and file integrity requirements
before allowing ZIP exports, API exports, or GitHub pushes.
"""

import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.execution.models import ExportValidationResult, ExportResult

_logger = logging.getLogger("aiforge.exporter.gate")


class ExportGate:
    """
    Single authoritative export gate for AIForge.
    All export entry points (ZIP, API, GitHub, Docs) must invoke validate_state().
    """

    def compute_project_hash(self, files: Dict[str, str]) -> str:
        """Computes a deterministic MD5 hash over sorted project file paths and contents."""
        if not files:
            return ""
        sorted_pairs = sorted(files.items(), key=lambda x: x[0])
        combined = "\n".join([f"{path}:{content}" for path, content in sorted_pairs])
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def mark_verified(self, state: Dict[str, Any]) -> str:
        """Calculates and stores verification hash and timestamp on ProjectState when tests pass."""
        files = state.get("files", {}) or {}
        v_hash = self.compute_project_hash(files)
        state["verified_project_hash"] = v_hash
        state["verified_at"] = datetime.now(timezone.utc).isoformat()
        return v_hash

    def validate_state(self, state: Dict[str, Any], project_path: Optional[str] = None) -> ExportValidationResult:
        """
        Independently validates execution, testing, project status, path security, and file integrity.
        Returns ExportValidationResult(allowed=True/False, reason=..., checks=...).
        """
        checks: Dict[str, bool] = {}
        denial_reasons = []

        # 1. Execution Evidence
        exec_res = state.get("execution_results", {}) or {}
        exec_exit = exec_res.get("exit_code") == 0
        exec_status = exec_res.get("status") == "PASS"
        has_exec = ("exit_code" in exec_res and "status" in exec_res)
        checks["execution_passed"] = bool(has_exec and exec_exit and exec_status)
        if not checks["execution_passed"]:
            denial_reasons.append("Execution evidence missing or failed (exit_code != 0 or status != PASS)")

        # 2. Testing Evidence
        test_res = state.get("test_results", {}) or {}
        test_success = test_res.get("success") is True
        test_failed_count = test_res.get("failed", 0) == 0
        has_test = ("success" in test_res)
        checks["testing_passed"] = bool(has_test and test_success and test_failed_count)
        if not checks["testing_passed"]:
            denial_reasons.append("Testing evidence missing or failed (success != True or failed > 0)")

        # 3. Overall Project Status
        proj_status = state.get("status", "")
        checks["status_is_pass"] = (proj_status == "PASS")
        if not checks["status_is_pass"]:
            denial_reasons.append(f"Project status is '{proj_status}', expected 'PASS'")

        # 4. Explicit Denial of Unresolved Terminal Failures
        unresolved_terminal_states = [
            "FAILED", "FAILED_MAX_ITERATIONS", "UNSUPPORTED",
            "SECURITY_ERROR", "TIMEOUT", "COMPILE_ERROR"
        ]
        checks["no_unresolved_terminal_failure"] = (proj_status not in unresolved_terminal_states)
        if not checks["no_unresolved_terminal_failure"]:
            denial_reasons.append(f"Project terminated with unresolved failure status '{proj_status}'")

        # 5. Project Directory & Path Traversal Security
        path_str = state.get("project_path") or project_path or ""
        path_valid = False
        if path_str:
            clean_path = path_str.replace("\\", "/")
            if "../" not in clean_path and "..\\" not in clean_path and not (clean_path.startswith("/") and not clean_path.startswith("//") and not clean_path.startswith("/tmp") and len(clean_path) < 5):
                try:
                    target_dir = Path(path_str).resolve()
                    path_valid = target_dir.exists() and target_dir.is_dir()
                except Exception:
                    path_valid = False

        checks["project_path_valid"] = path_valid
        if not path_valid:
            denial_reasons.append(f"Invalid or missing project directory path '{path_str}'")

        # 6. Non-empty Project Files & Traversal Check
        files = state.get("files", {}) or {}
        has_files = len(files) > 0
        no_traversal_files = True
        for rel_f in files.keys():
            raw_f = str(rel_f).replace("\\", "/")
            if raw_f.startswith("/") or raw_f.startswith("\\") or "../" in raw_f or "..\\" in raw_f or ":" in raw_f:
                no_traversal_files = False
                break
        checks["files_valid"] = bool(has_files and no_traversal_files)
        if not checks["files_valid"]:
            denial_reasons.append("Project has no files or contains invalid path traversal file entries")


        # 7. Stale Verification Protection (File Integrity Verification)
        verified_hash = state.get("verified_project_hash", "")
        current_hash = self.compute_project_hash(files) if files else ""
        if verified_hash:
            checks["file_integrity_verified"] = (current_hash == verified_hash)
            if not checks["file_integrity_verified"]:
                denial_reasons.append("Project files were modified after verification passed. Re-verification required")
        else:
            checks["file_integrity_verified"] = True

        # 8. Requirement Fidelity & Intent Alignment Gate
        req_fid = state.get("requirement_fidelity", {}) or {}
        if req_fid:
            fid_status = req_fid.get("status") == "PASS"
            domain_matched = req_fid.get("domain_matched", True)
            checks["requirement_fidelity_passed"] = bool(fid_status and domain_matched)
            if not checks["requirement_fidelity_passed"]:
                denial_reasons.append("Requirement Fidelity Failed: " + req_fid.get("reason", "Project context does not match user prompt"))
        else:
            checks["requirement_fidelity_passed"] = True

        allowed = all(checks.values())
        reason = "Project verification passed cleanly." if allowed else ("Export Denied: " + "; ".join(denial_reasons))


        return ExportValidationResult(
            allowed=allowed,
            reason=reason,
            checks=checks,
            verification_hash=current_hash,
            verified_at=state.get("verified_at")
        )


global_export_gate = ExportGate()
