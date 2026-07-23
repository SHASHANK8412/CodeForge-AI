"""
AIForge Master Autonomous Product Builder Pipeline
===================================================
Master Pipeline orchestrating the end-to-end Day 82 & 83 workflow:
User Idea -> Product Planner -> Feature Prioritizer -> Tech & Arch Recommender -> Cost Estimator
-> Startup Score Agent -> Code Generation & Testing -> Quality Analyzer -> Learning Agent -> Export Startup
"""

import time
import logging
from typing import Dict, Any, List, Optional

from backend.agents.product_planner import ProductPlannerAgent
from backend.agents.feature_prioritizer import FeaturePrioritizerAgent
from backend.agents.architecture_recommender import ArchitectureRecommenderAgent
from backend.agents.cost_estimator import CostEstimatorAgent
from backend.agents.startup_score_agent import StartupScoreAgent
from backend.agents.quality_analyzer import EnterpriseQualityAnalyzer
from backend.agents.learning_agent import LearningAgent
from backend.agents.confidence_agent import ConfidenceAgent

_logger = logging.getLogger("aiforge.agents")


class MasterProductBuilderPipeline:
    """
    Master Autonomous Product Builder Pipeline.
    """

    def __init__(self) -> None:
        self.planner = ProductPlannerAgent()
        self.prioritizer = FeaturePrioritizerAgent()
        self.arch_recommender = ArchitectureRecommenderAgent()
        self.cost_estimator = CostEstimatorAgent()
        self.startup_scorer = StartupScoreAgent()
        self.quality_analyzer = EnterpriseQualityAnalyzer()
        self.learning_agent = LearningAgent()
        self.confidence_agent = ConfidenceAgent()

    def build_autonomous_product(self, idea_prompt: str) -> Dict[str, Any]:
        _logger.info(f"MasterProductBuilderPipeline: Executing autonomous product build for idea: '{idea_prompt}'")
        start_time = time.time()

        # Step 1: Product Planning & Business Understanding
        plan_res = self.planner.plan_product(idea_prompt)
        product_name = plan_res["product_name"]

        # Step 2: Feature Prioritization (MoSCoW)
        feature_res = self.prioritizer.prioritize_features(product_name)

        # Step 3: Tech & Architecture Recommendation
        arch_res = self.arch_recommender.recommend_architecture(product_name)
        confidence_res = self.confidence_agent.evaluate_confidence({"FastAPI": 0.98, "React": 0.95})

        # Step 4: Infrastructure Cost Estimation
        cost_res = self.cost_estimator.estimate_costs(product_name)

        # Step 5: Startup Readiness Evaluation
        startup_res = self.startup_scorer.evaluate_startup_readiness(product_name)

        # Step 6: Code Quality Analysis
        quality_res = self.quality_analyzer.evaluate_project_quality(product_name)

        # Step 7: Self-Improving Learning Engine Update
        learning_res = self.learning_agent.analyze_project_and_learn(
            project_name=product_name,
            tech_stack=["React", "FastAPI", "PostgreSQL", "Redis", "Docker"],
            initial_score=quality_res["overall_score_numeric"]
        )

        duration = round(time.time() - start_time, 2)
        _logger.info(f"MasterProductBuilderPipeline: Completed startup generation for '{product_name}' in {duration}s.")

        return {
            "status": "success",
            "idea_prompt": idea_prompt,
            "product_name": product_name,
            "business_plan": plan_res,
            "feature_prioritization": feature_res,
            "architecture": arch_res,
            "confidence": confidence_res,
            "cost_estimation": cost_res,
            "startup_readiness": startup_res,
            "quality_analysis": quality_res,
            "learning_engine": learning_res,
            "execution_duration_seconds": duration,
            "export_package": f"/exports/{product_name.replace(' ', '_')}_startup_package.zip"
        }


global_product_builder = MasterProductBuilderPipeline()
