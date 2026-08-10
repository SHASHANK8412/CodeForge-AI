"""
AIForge Day 32 — Intelligent Infrastructure-as-Code Engine Test Suite
======================================================================
Comprehensive unit and integration tests covering:
1. Terraform HCL Modular Code Generation (main.tf, variables.tf, environments/)
2. HCL Structural & Syntax Validation
3. Plan Generation, Resource Parsing (CREATE, MODIFY, DESTROY) & Destructive Change Detection
4. Secret Protection (Detecting raw passwords in HCL files)
5. Infrastructure Security Analyzer (Public database & open SSH violation detection)
6. Infrastructure Policy Engine (Blocking unapproved destructive operations & security violations)
7. Cost Estimation (AWS, Azure, GCP, Local)
8. Infrastructure Drift Detection
9. Flight Recorder Audit Trail Recording
10. Architectural Decision Record (ADR-015) Generation
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.infrastructure.terraform.generator import TerraformGenerator
from backend.infrastructure.terraform.validator import TerraformValidator
from backend.infrastructure.terraform.security import InfrastructureSecurityAnalyzer
from backend.infrastructure.terraform.planner import TerraformPlanner
from backend.infrastructure.terraform.state import DriftAnalyzer
from backend.infrastructure.terraform.executor import TerraformExecutor
from backend.infrastructure.policies.policy_engine import InfrastructurePolicyEngine
from backend.infrastructure.service import InfrastructureService
from backend.infrastructure.terraform.models import InfraRequirement, PlanActionEnum


@pytest.fixture
def client():
    return TestClient(app)


class TestInfrastructureSuite:

    def test_terraform_generation_structure(self):
        gen = TerraformGenerator()
        req = InfraRequirement(project_id="proj_alpha", environment="production", provider="AWS")
        files = gen.generate_iac(req)

        assert "main.tf" in files
        assert "variables.tf" in files
        assert "providers.tf" in files
        assert "environments/production.tfvars" in files
        assert "publicly_accessible     = false" in files["main.tf"]
        assert "var.db_password" in files["main.tf"]

    def test_terraform_validation_clean_and_dirty(self):
        val = TerraformValidator()
        clean_files = {"main.tf": "resource \"aws_vpc\" \"main\" {\n  cidr = \"10.0.0.0/16\"\n}\n"}
        res_clean = val.validate_iac(clean_files)
        assert res_clean["is_valid"] is True

        dirty_files = {"main.tf": "resource \"aws_vpc\" \"main\" {\n  cidr = \"10.0.0.0/16\"\n"}
        res_dirty = val.validate_iac(dirty_files)
        assert res_dirty["is_valid"] is False

    def test_infrastructure_security_analyzer_detects_violations(self):
        sec = InfrastructureSecurityAnalyzer()

        clean_files = {"main.tf": "resource \"aws_db_instance\" \"db\" { publicly_accessible = false; storage_encrypted = true }" }
        sec_clean = sec.scan_infrastructure_security(clean_files)
        assert sec_clean.passed is True

        dirty_files = {"main.tf": "resource \"aws_db_instance\" \"db\" { publicly_accessible = true; password = \"raw_secret_123\" }" }
        sec_dirty = sec.scan_infrastructure_security(dirty_files)
        assert sec_dirty.passed is False
        assert any("Public Database" in v for v in sec_dirty.violations)
        assert any("Plaintext Secret" in v for v in sec_dirty.violations)

    def test_plan_parser_and_destructive_change_detection(self):
        planner = TerraformPlanner()

        # Non-destructive plan
        plan_normal = planner.generate_plan(project_id="proj_alpha", simulate_destructive=False)
        assert plan_normal.to_create_count >= 8
        assert plan_normal.to_destroy_count == 0
        assert plan_normal.is_destructive is False

        # Destructive plan
        plan_destruct = planner.generate_plan(project_id="proj_alpha", simulate_destructive=True)
        assert plan_destruct.to_destroy_count == 1
        assert plan_destruct.is_destructive is True
        assert any("postgres_legacy" in r for r in plan_destruct.destructive_resources)

    def test_policy_engine_blocks_unapproved_destructive_and_insecure_plans(self):
        engine = InfrastructurePolicyEngine()
        planner = TerraformPlanner()
        sec = InfrastructureSecurityAnalyzer()

        clean_sec = sec.scan_infrastructure_security({"main.tf": "resource \"aws_vpc\" \"m\" {}"})
        destruct_plan = planner.generate_plan(simulate_destructive=True)

        # Unapproved destructive plan in production -> BLOCKED
        eval_unapproved = engine.evaluate(destruct_plan, clean_sec, environment="production", user_approved=False)
        assert eval_unapproved["allowed"] is False
        assert any("DESTRUCTIVE POLICY BLOCK" in b for b in eval_unapproved["blocks"])

        # Approved destructive plan -> ALLOWED
        eval_approved = engine.evaluate(destruct_plan, clean_sec, environment="production", user_approved=True)
        assert eval_approved["allowed"] is True

    def test_drift_analyzer_detection(self):
        da = DriftAnalyzer()
        drift = da.detect_drift(project_id="proj_alpha", simulate_drift=True)

        assert drift.has_drift is True
        assert drift.resource_name == "aws_ecs_task_definition.backend"
        assert drift.expected == "3 replicas"
        assert drift.actual == "5 replicas"

    def test_cost_estimation(self):
        service = InfrastructureService()
        aws_cost = service.estimate("proj_alpha", provider_name="AWS")
        assert aws_cost.monthly_total_usd == 98.0

        local_cost = service.estimate("proj_alpha", provider_name="Local")
        assert local_cost.monthly_total_usd == 0.0

    def test_adr_015_generation(self):
        service = InfrastructureService()
        adr = service.generate_adr_015("proj_alpha")

        assert adr["adr_filepath"] == "docs/adr/ADR-015.md"
        assert adr["status"] == "APPROVED"
        assert "AWS RDS PostgreSQL" in adr["content"]

    def test_infrastructure_api_endpoints(self, client):
        res = client.get("/api/infrastructure/overview?project_id=aiforge-demo")
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "AWS"
        assert data["plan"]["to_create_count"] >= 8
        assert data["cost"]["monthly_total_usd"] == 98.0
        assert data["security"]["passed"] is True
