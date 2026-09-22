import os
import sys
import asyncio
from pathlib import Path

# Ensure PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.requirements.product_intelligence_agent import global_product_intelligence_agent
from backend.requirements.ambiguity_detector import global_ambiguity_detector
from backend.requirements.traceability_engine import global_traceability_engine
from backend.requirements.impact_analyzer import global_change_impact_analyzer
from backend.requirements.specification_manager import global_specification_manager


def run_requirements_acceptance():
    print("=" * 75)
    print("AIForge Product Intelligence & Requirements Engineering Acceptance Test")
    print("=" * 75)

    proj_dir = Path("./generated_projects/FoodDeliveryPlatform").resolve()
    proj_dir.mkdir(parents=True, exist_ok=True)

    # Acceptance Test 1: "Build a full-stack food delivery platform."
    prompt1 = "Build a full-stack food delivery platform with user authentication, restaurant menus, cart, and order tracking."
    print(f"\n[RUN] [1/6] Processing User Request: '{prompt1}'")

    spec = global_product_intelligence_agent.analyze_prompt(prompt1, "FoodDeliveryPlatform")
    print(f"[OK] [2/6] Product Intelligence Spec v{spec.version} Extracted: {len(spec.functional_requirements)} FRs, {len(spec.security_requirements)} SECs, {len(spec.user_stories)} USs, {len(spec.acceptance_criteria)} ACs")
    assert len(spec.functional_requirements) >= 4
    assert any(r.id == "FR-001" for r in spec.functional_requirements)
    assert any(r.id == "SEC-001" for r in spec.security_requirements)

    ambiguities = global_ambiguity_detector.detect_ambiguities(prompt1)
    spec.open_questions = ambiguities
    print(f"[OK] [3/6] Ambiguity Detector Identified {len(ambiguities)} High-Value Clarification Question(s)")

    global_specification_manager.save_specification("FoodDeliveryPlatform", spec, proj_dir)
    assert (proj_dir / "REQUIREMENTS.md").exists()
    print("[OK] [4/6] REQUIREMENTS.md Disk Specification Generated Successfully!")

    # Acceptance Test 2: Incremental Change Request "Add Google login"
    change_prompt = "Add Google OAuth 2.0 login."
    print(f"\n[RUN] [5/6] Processing Incremental Change Request: '{change_prompt}'")

    existing_files = {
        "backend/main.py": "from fastapi import FastAPI\napp=FastAPI()",
        "backend/auth.py": "def login(): pass",
        "frontend/src/pages/Login.jsx": "export default function Login(){}"
    }

    impact = global_change_impact_analyzer.analyze_change(change_prompt, spec, existing_files)
    updated_spec = global_specification_manager.apply_change_impact("FoodDeliveryPlatform", impact, proj_dir)

    print(f"[OK] [6/6] Change Impact Analyzed: Updated Spec to v{updated_spec.version}, New Requirements: {[r.id for r in impact.new_requirements]}, Affected Files: {impact.affected_files}")
    assert updated_spec.version == "1.1"
    assert any("FR-019" in r.id for r in updated_spec.functional_requirements)
    assert impact.requires_full_regeneration is False

    print("\n[SUCCESS] ALL PRODUCT INTELLIGENCE & REQUIREMENTS ACCEPTANCE TESTS PASSED!\n")


if __name__ == "__main__":
    run_requirements_acceptance()
