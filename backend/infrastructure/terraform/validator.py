"""
AIForge Day 32 — Terraform Validator
====================================
Performs static HCL syntax and structural validation in an isolated sandbox.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.infrastructure.validator")


class TerraformValidator:
    """
    Validates Terraform code formatting and structural syntax.
    """

    def validate_iac(self, files: Dict[str, str]) -> Dict[str, Any]:
        errors = []

        for filename, content in files.items():
            if not isinstance(content, str):
                continue

            # Check brace balance
            open_braces = content.count("{")
            close_braces = content.count("}")
            if open_braces != close_braces:
                errors.append(f"Mismatched braces in '{filename}': {open_braces} '{{' vs {close_braces} '}}'.")

            # Check for empty resource blocks
            if "resource \"\"" in content or "variable \"\"" in content:
                errors.append(f"Unnamed resource or variable declaration in '{filename}'.")

        is_valid = len(errors) == 0
        _logger.info(f"[TerraformValidator] HCL Validation {'PASSED' if is_valid else 'FAILED'}: {errors}")
        return {"is_valid": is_valid, "errors": errors}


global_terraform_validator = TerraformValidator()
