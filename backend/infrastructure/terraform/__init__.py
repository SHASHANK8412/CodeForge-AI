"""
AIForge Day 32 — Terraform IaC Submodule
"""
from backend.infrastructure.terraform.generator import global_terraform_generator
from backend.infrastructure.terraform.validator import global_terraform_validator
from backend.infrastructure.terraform.security import global_infra_security_analyzer
from backend.infrastructure.terraform.planner import global_terraform_planner
from backend.infrastructure.terraform.state import global_drift_analyzer
from backend.infrastructure.terraform.executor import global_terraform_executor

__all__ = [
    "global_terraform_generator",
    "global_terraform_validator",
    "global_infra_security_analyzer",
    "global_terraform_planner",
    "global_drift_analyzer",
    "global_terraform_executor"
]
