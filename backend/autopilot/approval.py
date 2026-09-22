"""
AIForge V2 — Engineering Autopilot Approval Manager
===================================================
Manages configurable human approval gates before high-risk or destructive actions:
- Production deployment
- Database schema destruction
- Major architecture changes
"""

import time
import secrets
import logging
from typing import Dict, Any, List, Optional

from backend.autopilot.models import ApprovalRequest

_logger = logging.getLogger("aiforge.autopilot.approval")


class ApprovalManager:
    """
    Manages human approval requests and approval gate enforcement for Autopilot.
    """

    def __init__(self):
        self._pending: Dict[str, List[ApprovalRequest]] = {}  # gen_id -> [ApprovalRequest]

    def create_request(
        self,
        generation_id: str,
        action: str,
        reason: str
    ) -> ApprovalRequest:
        req_id = f"appr_{secrets.token_urlsafe(8)}"
        req = ApprovalRequest(
            id=req_id,
            generation_id=generation_id,
            action=action,
            reason=reason,
            status="PENDING",
            created_at=time.strftime("%H:%M:%S")
        )

        requests = self._pending.setdefault(generation_id, [])
        requests.append(req)
        _logger.info(f"ApprovalManager: Created approval request '{action}' for generation '{generation_id}'")
        return req

    def get_pending_request(self, generation_id: str) -> Optional[ApprovalRequest]:
        requests = self._pending.get(generation_id, [])
        for r in requests:
            if r.status == "PENDING":
                return r
        return None

    def approve_request(self, generation_id: str, request_id: str) -> bool:
        requests = self._pending.get(generation_id, [])
        for r in requests:
            if r.id == request_id and r.status == "PENDING":
                r.status = "APPROVED"
                _logger.info(f"ApprovalManager: Approved request '{request_id}' for generation '{generation_id}'")
                return True
        return False

    def reject_request(self, generation_id: str, request_id: str) -> bool:
        requests = self._pending.get(generation_id, [])
        for r in requests:
            if r.id == request_id and r.status == "PENDING":
                r.status = "REJECTED"
                _logger.info(f"ApprovalManager: Rejected request '{request_id}' for generation '{generation_id}'")
                return True
        return False


global_approval_manager = ApprovalManager()
