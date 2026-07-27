"""
AIForge Architecture Package
============================
Requirement Analyzer, Core Architecture Designer, API Designer, Database Designer, Scalability Planner, Risk Analyzer, and Diagram Generator.
"""

from backend.architecture.analyzer import RequirementAnalyzer, global_requirement_analyzer
from backend.architecture.designer import CoreArchitectureDesigner, ArchitecturePattern, global_core_architecture_designer
from backend.architecture.api_designer import APIDesigner, global_api_designer
from backend.architecture.database_designer import DatabaseDesigner, global_database_designer
from backend.architecture.scalability import ScalabilityPlanner, global_scalability_planner
from backend.architecture.risk_analyzer import RiskAnalyzer, global_risk_analyzer
from backend.architecture.diagrams import ArchitectureDiagramGenerator, global_architecture_diagram_generator

__all__ = [
    "RequirementAnalyzer", "global_requirement_analyzer",
    "CoreArchitectureDesigner", "ArchitecturePattern", "global_core_architecture_designer",
    "APIDesigner", "global_api_designer",
    "DatabaseDesigner", "global_database_designer",
    "ScalabilityPlanner", "global_scalability_planner",
    "RiskAnalyzer", "global_risk_analyzer",
    "ArchitectureDiagramGenerator", "global_architecture_diagram_generator"
]
