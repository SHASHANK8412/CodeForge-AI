"""
AIForge Open Policy Agent (OPA) Security & Authorization Engine
================================================================
Enforces enterprise security policies, role-based authorization (RBAC), and regulatory compliance rules on generated code and API actions.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.security.opa_engine")


class OPAPolicyEngine:
    """
    Open Policy Agent (OPA) Rego policy enforcement simulator for enterprise authorization and code safety checks.
    """

    def evaluate_policy(self, input_context: Dict[str, Any], policy_name: str = "security_policy") -> Dict[str, Any]:
        """
        Evaluates Rego authorization and safety policies against the provided input context.
        """
        role = input_context.get("role", "developer")
        action = input_context.get("action", "generate_code")
        code = input_context.get("code", "")

        violations = []

        # Policy Rule 1: No hardcoded secrets / API keys in code
        if "api_key =" in code.lower() or "secret_key =" in code.lower() or "password =" in code.lower():
            violations.append("Policy Violation [OPA-SEC-01]: Hardcoded plaintext secret detected in generated code.")

        # Policy Rule 2: Unsafe eval / exec usage
        if "eval(" in code or "exec(" in code:
            violations.append("Policy Violation [OPA-SEC-02]: Unsafe eval/exec execution keyword detected.")

        # Policy Rule 3: Admin deployment restriction
        if action == "deploy_production" and role not in ["admin", "devops_lead"]:
            violations.append("Policy Violation [OPA-AUTH-01]: Role is unauthorized for production deployment.")

        is_allowed = len(violations) == 0
        _logger.info(f"OPAPolicyEngine: Evaluated policy '{policy_name}' for action '{action}' -> Allowed: {is_allowed}")

        return {
            "policy_name": policy_name,
            "is_allowed": is_allowed,
            "violations_count": len(violations),
            "violations": violations
        }


global_opa_policy_engine = OPAPolicyEngine()
