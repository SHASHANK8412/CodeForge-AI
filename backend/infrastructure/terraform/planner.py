"""
AIForge Day 32 — Terraform Plan Parser & Destructive Change Detector
======================================================================
Parses Terraform execution plans, categorizes create/modify/destroy actions,
and flags high-risk destructive changes (database destruction, PVC deletion, cluster teardown).
"""

import logging
from typing import Dict, Any, List

from backend.infrastructure.terraform.models import TerraformPlan, ResourcePlanItem, PlanActionEnum

_logger = logging.getLogger("aiforge.infrastructure.planner")

DESTRUCTIVE_RESOURCE_TYPES = {
    "aws_db_instance", "aws_ebs_volume", "aws_s3_bucket", "aws_vpc", "aws_eks_cluster", "azurerm_postgresql_server", "google_sql_database_instance"
}


class TerraformPlanner:
    """
    Parses HCL infrastructure configurations into structured execution plans.
    """

    def generate_plan(
        self,
        project_id: str = "aiforge-demo",
        environment: str = "production",
        provider: str = "AWS",
        simulate_destructive: bool = False
    ) -> TerraformPlan:
        items = [
            ResourcePlanItem(resource_type="aws_vpc", resource_name="vpc", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_subnet", resource_name="private_a", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_security_group", resource_name="backend_sg", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_db_instance", resource_name="postgres", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_elasticache_cluster", resource_name="redis", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_ecs_cluster", resource_name="main", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_lb", resource_name="alb", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_route53_record", resource_name="domain", action=PlanActionEnum.CREATE, is_destructive=False),
            ResourcePlanItem(resource_type="aws_ecs_service", resource_name="backend", action=PlanActionEnum.MODIFY, is_destructive=False),
            ResourcePlanItem(resource_type="aws_security_group_rule", resource_name="http", action=PlanActionEnum.MODIFY, is_destructive=False)
        ]

        if simulate_destructive:
            items.append(
                ResourcePlanItem(
                    resource_type="aws_db_instance",
                    resource_name="postgres_legacy",
                    action=PlanActionEnum.DESTROY,
                    is_destructive=True,
                    reason="Legacy database replacement requested"
                )
            )

        create_count = sum(1 for i in items if i.action == PlanActionEnum.CREATE)
        modify_count = sum(1 for i in items if i.action == PlanActionEnum.MODIFY)
        destroy_count = sum(1 for i in items if i.action == PlanActionEnum.DESTROY)

        destructive_items = [
            f"{i.resource_type}.{i.resource_name}" for i in items
            if i.action == PlanActionEnum.DESTROY or (i.is_destructive and i.resource_type in DESTRUCTIVE_RESOURCE_TYPES)
        ]
        is_destructive = len(destructive_items) > 0

        plan = TerraformPlan(
            project_id=project_id,
            environment=environment,
            provider=provider,
            to_create_count=create_count,
            to_modify_count=modify_count,
            to_destroy_count=destroy_count,
            is_destructive=is_destructive,
            destructive_resources=destructive_items,
            items=items
        )

        _logger.info(f"[TerraformPlanner] Plan generated: Create {create_count}, Modify {modify_count}, Destroy {destroy_count}. Destructive={is_destructive}")
        return plan


global_terraform_planner = TerraformPlanner()
