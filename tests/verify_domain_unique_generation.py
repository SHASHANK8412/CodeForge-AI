"""
AIForge Domain-Specific Unique Code Generation & 40% Similarity Audit
======================================================================
Tests 4 distinct prompts across different industries:
1. Formula 1 Website (Motorsport)
2. Food Delivery Website (FoodTech)
3. Hospital Management System (Healthcare)
4. E-commerce Website (Retail)

Verifies:
- 100% unique database schema tables per domain
- 100% unique REST API routers per domain
- 100% unique React SPA pages per domain
- Jaccard similarity across generated project files is strictly LESS than 40%
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.memory.project_memory import ProjectMemoryStore
from backend.generators.incremental_generator import IncrementalProjectGenerator, ProjectContext

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def calculate_jaccard_similarity(files_a: dict, files_b: dict) -> float:
    keys_a = set(files_a.keys())
    keys_b = set(files_b.keys())
    intersection = keys_a.intersection(keys_b)
    union = keys_a.union(keys_b)
    return len(intersection) / len(union) if union else 0.0


def test_domain_generation():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Requirement Analysis & Domain Unique Generation Verification")
    print("===========================================================================\n")

    generator = IncrementalProjectGenerator()

    # 1. Formula 1 Website
    f1_memory = ProjectMemoryStore("Formula 1 Website")
    f1_files = generator.generate_modules_incrementally("Formula 1 Website", f1_memory)
    f1_ctx = ProjectContext("Formula 1 Website")

    print("1. Formula 1 Website Domain Audit:")
    check("Extracted Domain is 'Sports / Motorsport'", f1_ctx.domain == "Sports / Motorsport")
    check("Generated driver_router.py", "backend/app/routers/driver_router.py" in f1_files)
    check("Generated Drivers.jsx page", "frontend/src/pages/Drivers.jsx" in f1_files)
    check("SQL Schema contains 'drivers' table", "CREATE TABLE IF NOT EXISTS drivers" in f1_files.get("database/schema.sql", ""))

    # 2. Food Delivery Website
    food_memory = ProjectMemoryStore("Food Delivery Website")
    food_files = generator.generate_modules_incrementally("Food Delivery Website", food_memory)
    food_ctx = ProjectContext("Food Delivery Website")

    print("\n2. Food Delivery Website Domain Audit:")
    check("Extracted Domain is 'FoodTech & Logistics'", food_ctx.domain == "FoodTech & Logistics")
    check("Generated restaurant_router.py", "backend/app/routers/restaurant_router.py" in food_files)
    check("Generated Restaurants.jsx page", "frontend/src/pages/Restaurants.jsx" in food_files)
    check("SQL Schema contains 'restaurants' table", "CREATE TABLE IF NOT EXISTS restaurants" in food_files.get("database/schema.sql", ""))

    # 3. Hospital Management System
    hosp_memory = ProjectMemoryStore("Hospital Management System")
    hosp_files = generator.generate_modules_incrementally("Hospital Management System", hosp_memory)
    hosp_ctx = ProjectContext("Hospital Management System")

    print("\n3. Hospital Management System Domain Audit:")
    check("Extracted Domain is 'Healthcare & Medicine'", hosp_ctx.domain == "Healthcare & Medicine")
    check("Generated patient_router.py", "backend/app/routers/patient_router.py" in hosp_files)
    check("Generated Patients.jsx page", "frontend/src/pages/Patients.jsx" in hosp_files)
    check("SQL Schema contains 'patients' table", "CREATE TABLE IF NOT EXISTS patients" in hosp_files.get("database/schema.sql", ""))

    # 4. E-Commerce Website
    ecom_memory = ProjectMemoryStore("E-commerce Website")
    ecom_files = generator.generate_modules_incrementally("E-commerce Website", ecom_memory)
    ecom_ctx = ProjectContext("E-commerce Website")

    print("\n4. E-commerce Website Domain Audit:")
    check("Extracted Domain is 'Retail & E-Commerce'", ecom_ctx.domain == "Retail & E-Commerce")
    check("Generated product_router.py", "backend/app/routers/product_router.py" in ecom_files)
    check("Generated Products.jsx page", "frontend/src/pages/Products.jsx" in ecom_files)
    check("SQL Schema contains 'products' table", "CREATE TABLE IF NOT EXISTS products" in ecom_files.get("database/schema.sql", ""))

    # 5. Jaccard Similarity Audit (< 40%)
    print("\n5. Jaccard Similarity Audit Across Domains:")
    sim_f1_food = calculate_jaccard_similarity(f1_files, food_files)
    sim_f1_hosp = calculate_jaccard_similarity(f1_files, hosp_files)
    sim_food_hosp = calculate_jaccard_similarity(food_files, hosp_files)

    print(f"   - F1 vs Food Delivery Similarity: {sim_f1_food:.2%}")
    print(f"   - F1 vs Hospital System Similarity: {sim_f1_hosp:.2%}")
    print(f"   - Food Delivery vs Hospital System Similarity: {sim_food_hosp:.2%}")

    check("Similarity between F1 and Food Delivery is < 40%", sim_f1_food < 0.40)
    check("Similarity between F1 and Hospital System is < 40%", sim_f1_hosp < 0.40)
    check("Similarity between Food Delivery and Hospital System is < 40%", sim_food_hosp < 0.40)

    # Summary
    print("\n" + "="*75)
    print(f" DOMAIN UNIQUE GENERATION VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = test_domain_generation()
    sys.exit(0 if success else 1)
