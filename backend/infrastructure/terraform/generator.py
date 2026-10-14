"""
AIForge Day 32 — Terraform HCL Generator
========================================
Generates modular Terraform infrastructure code (main.tf, variables.tf, outputs.tf, providers.tf,
locals.tf, environments/) with non-public database access, private networking, and secret references.
"""

import logging
from typing import Dict, Any, Optional

from backend.infrastructure.terraform.models import InfraRequirement

_logger = logging.getLogger("aiforge.infrastructure.generator")


class TerraformGenerator:
    """
    Generates standard modular Terraform IaC directory structure.
    """

    def generate_iac(self, req: InfraRequirement) -> Dict[str, str]:
        _logger.info(f"[TerraformGenerator] Generating IaC for project '{req.project_id}' on '{req.provider}' ({req.environment})")

        providers_tf = f"""terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}
"""

        variables_tf = f"""variable "project_id" {{
  type        = string
  default     = "{req.project_id}"
  description = "AIForge Project ID"
}}

variable "environment" {{
  type        = string
  default     = "{req.environment}"
  description = "Target deployment environment (development, staging, production)"
}}

variable "aws_region" {{
  type        = string
  default     = "us-east-1"
}}

variable "db_password" {{
  type        = string
  sensitive   = true
  description = "Managed Database Password passed via environment secret reference"
}}
"""

        locals_tf = f"""locals {{
  common_tags = {{
    Project     = var.project_id
    Environment = var.environment
    ManagedBy   = "AIForge-IaC"
  }}
}}
"""

        main_tf = f"""# AIForge Modular Infrastructure — Main Architecture
module "vpc" {{
  source = "./modules/vpc"
  cidr   = "10.0.0.0/16"
  tags   = local.common_tags
}}

resource "aws_db_instance" "postgres" {{
  allocated_storage       = 20
  engine                  = "postgres"
  engine_version          = "15.3"
  instance_class          = "db.t3.micro"
  db_name                 = "aiforge_db"
  username                = "aiforge_user"
  password                = var.db_password
  publicly_accessible     = false
  storage_encrypted       = true
  skip_final_snapshot     = true
  tags                    = local.common_tags
}}

resource "aws_elasticache_cluster" "redis" {{
  cluster_id           = "aiforge-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  tags                 = local.common_tags
}}

resource "aws_security_group" "backend_sg" {{
  name        = "{req.project_id}-backend-sg"
  description = "Security Group for Backend Compute"

  ingress {{
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }}

  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}
"""

        outputs_tf = """output "database_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "Private PostgreSQL DB Endpoint"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.redis.cache_nodes.0.address
  description = "Private Redis Endpoint"
}
"""

        env_tf = f"""# Environment Override ({req.environment})
environment = "{req.environment}"
"""

        return {
          "providers.tf": providers_tf,
          "variables.tf": variables_tf,
          "locals.tf": locals_tf,
          "main.tf": main_tf,
          "outputs.tf": outputs_tf,
          f"environments/{req.environment}.tfvars": env_tf
        }


global_terraform_generator = TerraformGenerator()
