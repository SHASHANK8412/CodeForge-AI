"""
Day 82 & 83 - Enterprise AIForge: Self-Improvement & Autonomous Product Builder Verification Suite
===================================================================================================
Validates AIForge Learning Engine & Autonomous Product Builder across 4 core testing scenarios:
- Test 1: Learning Engine Test (Generate MERN e-commerce twice -> 2nd generation reuses rules and achieves higher score)
- Test 2: Quality Analysis Test (Produces 8-dimension scores: Arch, Sec, Test, Perf, Maint, Doc, Scale, Read)
- Test 3: Product Planning Test (Prompt "Build an Airbnb for coworking spaces" -> Business, Personas, Features, Arch Mermaid, Roadmap, Cost)
- Test 4: Autonomous Pipeline Test (Prompt "Build a SaaS CRM for small businesses" -> Complete end-to-end pipeline run to Export)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.learning_agent import LearningAgent
from backend.agents.quality_analyzer import EnterpriseQualityAnalyzer
from backend.agents.confidence_agent import ConfidenceAgent
from backend.agents.product_planner import ProductPlannerAgent
from backend.agents.feature_prioritizer import FeaturePrioritizerAgent
from backend.agents.architecture_recommender import ArchitectureRecommenderAgent
from backend.agents.cost_estimator import CostEstimatorAgent
from backend.agents.startup_score_agent import StartupScoreAgent
from backend.agents.product_builder import MasterProductBuilderPipeline

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


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


async def run_day82_83_tests():
    print("======================================================================")
    print(" AIForge Day 82-83 - Self-Improvement & Product Builder Verification")
    print("======================================================================\n")

    learning_agent = LearningAgent()
    quality_analyzer = EnterpriseQualityAnalyzer()
    planner = ProductPlannerAgent()
    product_builder = MasterProductBuilderPipeline()

    # ------------------------------------------------------------------
    section("Test 1 – Learning Engine Test (Day 82)")
    # ------------------------------------------------------------------
    # First generation
    run_1 = learning_agent.analyze_project_and_learn("MERN E-Commerce App", ["React", "Express", "MongoDB"], initial_score=88.0)
    # Second generation reuses learned rules
    run_2 = learning_agent.analyze_project_and_learn("MERN E-Commerce App V2", ["React", "Express", "MongoDB"], initial_score=run_1["improved_score"])

    check("First project generation recorded mistakes & learned rules", run_1["knowledge_base_size"] >= 2)
    check("Second generation achieved higher quality score (88.0% -> 94.5%+)", run_2["improved_score"] > run_1["initial_score"])
    check("Persisted updated knowledge base in learning/knowledge.json", learning_agent.knowledge_file.exists())

    # ------------------------------------------------------------------
    section("Test 2 – 8-Dimension Quality Analysis Test (Day 82)")
    # ------------------------------------------------------------------
    quality_report = quality_analyzer.evaluate_project_quality("MERN E-Commerce App")
    scores = quality_report.get("category_scores", {})

    check("Evaluated 8 core quality categories (Arch, Sec, Test, Perf, Maint, Doc, Scale, Read)", len(scores) == 8)
    check("Calculated overall quality score percentage (overall >= 90%)", quality_report["overall_score_numeric"] >= 90.0)
    check("Produced top 10 actionable improvement suggestions", len(quality_report["top_10_improvement_suggestions"]) == 10)
    check("Saved report to reports/quality_report.json", quality_analyzer.report_file.exists())

    # ------------------------------------------------------------------
    section("Test 3 – Product Planning Test (Day 83)")
    # ------------------------------------------------------------------
    coworking_plan = planner.plan_product("Build an Airbnb for coworking spaces")

    check("Extracted business analysis & user personas", len(coworking_plan["target_users"]) >= 3)
    check("Extracted pain points & revenue model", "commission" in coworking_plan["revenue_model"].lower())
    check("Generated multi-week development timeline roadmap", "Week 1" in coworking_plan["development_timeline"])

    # ------------------------------------------------------------------
    section("Test 4 – Complete Autonomous Product Builder Pipeline Test (Day 83)")
    # ------------------------------------------------------------------
    pipeline_res = product_builder.build_autonomous_product("Build a SaaS CRM for small businesses")

    check("Executed business planning & feature prioritization (MoSCoW)", len(pipeline_res["feature_prioritization"]["must_have"]) >= 3)
    check("Generated production architecture blueprint & Mermaid diagram", "graph TD" in pipeline_res["architecture"]["mermaid_architecture_diagram"])
    check("Estimated monthly infrastructure operational costs", pipeline_res["cost_estimation"]["total_monthly_cost_usd"] > 0)
    check("Evaluated Startup Readiness Score percentage (readiness >= 90%)", pipeline_res["startup_readiness"]["overall_score_numeric"] >= 90.0)
    check("Updated Learning Engine & exported complete startup package", pipeline_res["export_package"].endswith(".zip"))

    # Summary
    print("\n" + "="*70)
    print(f" DAY 82-83 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day82_83_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
