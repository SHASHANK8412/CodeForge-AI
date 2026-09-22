import os
import sys
import pytest
from pathlib import Path

# Ensure PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.requirements.product_intelligence_agent import global_product_intelligence_agent
from backend.requirements.ambiguity_detector import global_ambiguity_detector
from backend.requirements.traceability_engine import global_traceability_engine
from backend.requirements.impact_analyzer import global_change_impact_analyzer
from backend.requirements.specification_manager import global_specification_manager


class TestProductIntelligenceEngine:

    def test_product_intelligence_extraction(self):
        prompt = "Build a full-stack Food Delivery Platform with user authentication and order tracking."
        spec = global_product_intelligence_agent.analyze_prompt(prompt, "FoodDeliveryApp")

        assert spec.project_name == "FoodDeliveryApp"
        assert len(spec.functional_requirements) >= 4
        assert any(r.id == "FR-001" for r in spec.functional_requirements)
        assert any(r.id == "SEC-001" for r in spec.security_requirements)
        assert len(spec.user_stories) > 0
        assert len(spec.acceptance_criteria) > 0

    def test_ambiguity_detector(self):
        prompt = "Build an ecommerce food application with user login."
        ambiguities = global_ambiguity_detector.detect_ambiguities(prompt)

        assert len(ambiguities) > 0
        assert any(q.importance == "CRITICAL" or q.importance == "HIGH" for q in ambiguities)

    def test_traceability_engine(self):
        prompt = "Build a Todo Application."
        spec = global_product_intelligence_agent.analyze_prompt(prompt, "TodoAppTraceTest")

        files_manifest = {
            "backend/main.py": "from fastapi import FastAPI\napp=FastAPI()\n@app.post('/api/auth/login')\ndef login(): return {}",
            "backend/auth.py": "# JWT Authentication Middleware\ndef create_access_token(): pass",
            "frontend/src/App.jsx": "import React from 'react'; export default function App(){ return <div>Todos</div>; }",
            "tests/test_unit.py": "def test_login(): pass\ndef test_create_todo(): pass"
        }

        updated_spec = global_traceability_engine.build_matrix(spec, files_manifest)
        assert updated_spec.coverage_score > 0.0
        assert len(updated_spec.traceability_matrix) > 0

        # Verify FR-001 or FR-002 maps to implementation and test files
        fr1_trace = next((t for t in updated_spec.traceability_matrix if t.requirement_id in ["FR-001", "FR-002"]), None)
        assert fr1_trace is not None
        assert len(fr1_trace.implementation_files) > 0

    def test_change_impact_analyzer_incremental(self):
        prompt = "Build a Food Delivery Platform."
        spec = global_product_intelligence_agent.analyze_prompt(prompt, "ImpactTestApp")

        existing_files = {
            "backend/auth.py": "def login(): pass",
            "frontend/src/pages/Login.jsx": "export default function Login(){}"
        }

        impact = global_change_impact_analyzer.analyze_change("Add Google OAuth 2.0 Login", spec, existing_files)
        assert impact.requires_full_regeneration is False
        assert any(r.id == "FR-019" for r in impact.new_requirements)
        assert "BackendAgent" in impact.affected_agents

    def test_specification_manager_versioning(self, tmp_path):
        prompt = "Build Todo Application."
        spec = global_product_intelligence_agent.analyze_prompt(prompt, "SpecVersionApp")

        global_specification_manager.save_specification("SpecVersionApp", spec, tmp_path)
        assert (tmp_path / "REQUIREMENTS.md").exists()

        existing_files = {"backend/auth.py": "def login(): pass"}
        impact = global_change_impact_analyzer.analyze_change("Add Stripe Payments", spec, existing_files)
        updated_spec = global_specification_manager.apply_change_impact("SpecVersionApp", impact, tmp_path)

        assert updated_spec.version == "1.1"
        assert any("FR-020" in r.id for r in updated_spec.functional_requirements)
