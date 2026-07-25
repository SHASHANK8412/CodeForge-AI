"""
AIForge V2 – Planner Output Parser
==================================
Parses raw LLM markdown outputs into structured Pydantic PlannerReport models.
"""

import json
import logging
from typing import Dict, Any, Optional
from v2.agents.planner.models import (
    PlannerReport, BusinessAnalysis, FunctionalRequirement, NonFunctionalRequirement,
    UserPersona, UserStory, AcceptanceCriteria, PrioritizedFeature, MVPDefinition,
    SprintPlan, RiskItem, TechRecommendation, RequirementPriority, RiskSeverity
)

_logger = logging.getLogger("aiforge.v2.planner.parser")


class PlannerOutputParser:
    """
    Parses LLM JSON string or markdown code blocks into PlannerReport instances.
    """

    def parse_report(self, raw_output: str, project_id: str = "proj_v2_default") -> PlannerReport:
        try:
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_output.strip()

            data = json.loads(json_str)
        except Exception as exc:
            _logger.warning(f"PlannerOutputParser: Exception parsing JSON ({exc}). Using heuristic report construction.")
            data = {}

        proj_name = data.get("project_name") or "Software Project"
        biz_data = data.get("business_analysis", {})

        biz = BusinessAnalysis(
            project_name=biz_data.get("project_name", proj_name),
            business_goal=biz_data.get("business_goal", "Deliver high quality software solution."),
            target_users=biz_data.get("target_users", ["Primary User", "Administrator"]),
            core_features=biz_data.get("core_features", ["Authentication", "Dashboard", "Reporting"]),
            expected_scale=biz_data.get("expected_scale", "High performance multi-tenant architecture"),
            platforms=biz_data.get("platforms", ["Web SPA", "REST API"])
        )

        fr_raw = data.get("functional_requirements", [])
        frs_list = []
        for idx, item in enumerate(fr_raw):
            if isinstance(item, str):
                item = {"id": f"FR{idx+1}", "title": item, "description": item, "priority": "high"}
            elif not isinstance(item, dict):
                continue
            p_val = item.get("priority", "high")
            if not isinstance(p_val, str):
                p_val = "high"
            frs_list.append(
                FunctionalRequirement(
                    id=str(item.get("id", f"FR{idx+1}")),
                    title=str(item.get("title", f"Requirement {idx+1}")),
                    description=str(item.get("description", "System requirement capability.")),
                    priority=RequirementPriority(p_val.lower() if p_val.lower() in ["critical", "high", "medium", "low"] else "high")
                )
            )
        frs = frs_list or [
            FunctionalRequirement(id="FR1", title="User Authentication", description="Secure JWT authentication", priority=RequirementPriority.CRITICAL),
            FunctionalRequirement(id="FR2", title="Interactive Dashboard", description="Real-time data visualization dashboard", priority=RequirementPriority.HIGH),
            FunctionalRequirement(id="FR3", title="Data Export", description="Export project reports in CSV/PDF format", priority=RequirementPriority.MEDIUM)
        ]

        nfr_raw = data.get("non_functional_requirements", [])
        nfrs_list = []
        for item in nfr_raw:
            if isinstance(item, str):
                item = {"category": "Performance", "description": item, "target_metric": "<1.0s"}
            elif not isinstance(item, dict):
                continue
            nfrs_list.append(
                NonFunctionalRequirement(
                    category=str(item.get("category", "Performance")),
                    description=str(item.get("description", "System latency constraint.")),
                    target_metric=str(item.get("target_metric", "<1.0s"))
                )
            )
        nfrs = nfrs_list or [
            NonFunctionalRequirement(category="Performance", description="API Response Time", target_metric="<500ms"),
            NonFunctionalRequirement(category="Security", description="Data Encryption at Rest & Transit", target_metric="AES-256 / TLS 1.3"),
            NonFunctionalRequirement(category="Availability", description="Uptime Target SLA", target_metric="99.9%")
        ]

        personas_raw = data.get("user_personas", [])
        personas_list = []
        for p in personas_raw:
            if isinstance(p, str):
                p = {"name": p, "role": "User", "goals": [p], "pain_points": ["Manual process"], "needs": ["Automation"]}
            elif not isinstance(p, dict):
                continue
            personas_list.append(
                UserPersona(
                    name=str(p.get("name", "Standard User")),
                    role=str(p.get("role", "User")),
                    goals=p.get("goals") if isinstance(p.get("goals"), list) else ["Accomplish task efficiently"],
                    pain_points=p.get("pain_points") if isinstance(p.get("pain_points"), list) else ["Manual data entry"],
                    needs=p.get("needs") if isinstance(p.get("needs"), list) else ["Automation and fast UI"]
                )
            )
        personas = personas_list or [
            UserPersona(name="Primary User", role="End User", goals=["Streamline workflow"], pain_points=["Slow legacy apps"], needs=["Real-time AI assistance"])
        ]

        stories = []
        for idx, s in enumerate(data.get("user_stories", [])):
            if isinstance(s, str):
                s = {"id": f"US{idx+1}", "persona": "User", "i_want_to": s, "so_that": "achieve goal", "priority": "high", "acceptance_criteria": []}
            elif not isinstance(s, dict):
                continue
            ac_raw = s.get("acceptance_criteria", [])
            ac_list = []
            for ac in ac_raw if isinstance(ac_raw, list) else []:
                if isinstance(ac, str):
                    ac = {"given": "System ready", "when_event": ac, "then_outcome": "Outcome verified"}
                elif not isinstance(ac, dict):
                    continue
                ac_list.append(
                    AcceptanceCriteria(
                        given=str(ac.get("given", "System ready")),
                        when_event=str(ac.get("when_event", "Action triggered")),
                        then_outcome=str(ac.get("then_outcome", "Outcome verified"))
                    )
                )
            p_val = s.get("priority", "high")
            if not isinstance(p_val, str):
                p_val = "high"
            stories.append(
                UserStory(
                    id=str(s.get("id", f"US{idx+1}")),
                    persona=str(s.get("persona", "User")),
                    i_want_to=str(s.get("i_want_to", "perform key action")),
                    so_that=str(s.get("so_that", "achieve specific business outcome")),
                    priority=RequirementPriority(p_val.lower() if p_val.lower() in ["critical", "high", "medium", "low"] else "high"),
                    acceptance_criteria=ac_list
                )
            )

        if not stories:
            stories = [
                UserStory(
                    id="US1",
                    persona="Primary User",
                    i_want_to="sign in securely to the portal",
                    so_that="I can access my personal dashboard",
                    priority=RequirementPriority.CRITICAL,
                    acceptance_criteria=[AcceptanceCriteria(given="User provides valid credentials", when_event="Login submitted", then_outcome="JWT token returned and dashboard opens")]
                ),
                UserStory(
                    id="US2",
                    persona="Primary User",
                    i_want_to="submit data requests",
                    so_that="I can receive AI generated results",
                    priority=RequirementPriority.HIGH,
                    acceptance_criteria=[AcceptanceCriteria(given="Form completed", when_event="Submit clicked", then_outcome="Results display within 2 seconds")]
                )
            ]

        p_features = [
            PrioritizedFeature(
                feature_name=pf.get("feature_name", "Core Feature"),
                priority=RequirementPriority(pf.get("priority", "high").lower()),
                mvp_version=pf.get("mvp_version", "V1 (Must Have)")
            )
            for pf in data.get("prioritized_features", [])
        ] or [
            PrioritizedFeature(feature_name="User Authentication", priority=RequirementPriority.CRITICAL, mvp_version="V1 (Must Have)"),
            PrioritizedFeature(feature_name="Data Processing Pipeline", priority=RequirementPriority.HIGH, mvp_version="V1 (Must Have)"),
            PrioritizedFeature(feature_name="Analytics Dashboard", priority=RequirementPriority.MEDIUM, mvp_version="V2 (Should Have)")
        ]

        mvp_data = data.get("mvp_definition", {})
        mvp = MVPDefinition(
            v1_must_have=mvp_data.get("v1_must_have") or ["Authentication", "Core Pipeline", "API Endpoint"],
            v2_should_have=mvp_data.get("v2_should_have") or ["Analytics Dashboard", "Reporting Export"],
            v3_nice_to_have=mvp_data.get("v3_nice_to_have") or ["Third-party Webhooks", "Multi-language Support"]
        )

        sprints = [
            SprintPlan(
                sprint_number=int(sp.get("sprint_number", idx+1)),
                sprint_name=sp.get("sprint_name", f"Sprint {idx+1}"),
                duration_weeks=int(sp.get("duration_weeks", 2)),
                focus_area=sp.get("focus_area", "Engineering Deliverables"),
                deliverables=sp.get("deliverables", ["Core Modules"])
            )
            for idx, sp in enumerate(data.get("sprint_plan", []))
        ] or [
            SprintPlan(sprint_number=1, sprint_name="Sprint 1: Core Foundation", duration_weeks=2, focus_area="Architecture & Auth", deliverables=["JWT Auth", "PostgreSQL Schema"]),
            SprintPlan(sprint_number=2, sprint_name="Sprint 2: Backend API", duration_weeks=2, focus_area="API Routes", deliverables=["FastAPI Endpoints", "Pydantic Validation"]),
            SprintPlan(sprint_number=3, sprint_name="Sprint 3: Frontend UI", duration_weeks=2, focus_area="User Interface", deliverables=["React Components", "Dashboard Views"]),
            SprintPlan(sprint_number=4, sprint_name="Sprint 4: Testing & Hardening", duration_weeks=2, focus_area="QA & Security", deliverables=["Pytest Coverage", "Static Code Review"]),
            SprintPlan(sprint_number=5, sprint_name="Sprint 5: Deployment", duration_weeks=2, focus_area="DevOps", deliverables=["Docker Compose", "CI/CD Pipeline"])
        ]

        risks = [
            RiskItem(
                risk_type=r.get("risk_type", "Technical"),
                description=r.get("description", "Potential performance bottleneck."),
                severity=RiskSeverity(r.get("severity", "high").lower()),
                mitigation=r.get("mitigation", "Implement caching and connection pooling.")
            )
            for r in data.get("risk_analysis", [])
        ] or [
            RiskItem(risk_type="Technical", description="High traffic spikes impacting database latency", severity=RiskSeverity.HIGH, mitigation="Add Redis caching tier and connection pooling"),
            RiskItem(risk_type="Security", description="Unauthenticated API endpoint exposure", severity=RiskSeverity.CRITICAL, mitigation="Enforce strict OAuth2/JWT middleware checks")
        ]

        tech_recs = [
            TechRecommendation(
                layer=tr.get("layer", "Engineering"),
                technology=tr.get("technology", "React / FastAPI"),
                justification=tr.get("justification", "Proven production ecosystem.")
            )
            for tr in data.get("tech_recommendations", [])
        ] or [
            TechRecommendation(layer="Frontend", technology="React / Vite", justification="Fast HMR and component modularity"),
            TechRecommendation(layer="Backend", technology="FastAPI", justification="High performance async Python REST framework"),
            TechRecommendation(layer="Database", technology="PostgreSQL", justification="ACID compliant relational persistence"),
            TechRecommendation(layer="Cache", technology="Redis", justification="In-memory speed for session state and rate limiting")
        ]

        return PlannerReport(
            project_id=project_id,
            project_name=proj_name,
            business_analysis=biz,
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_personas=personas,
            user_stories=stories,
            prioritized_features=p_features,
            mvp_definition=mvp,
            sprint_plan=sprints,
            risk_analysis=risks,
            tech_recommendations=tech_recs,
            architecture_recommendation=data.get("architecture_recommendation", "Decoupled REST API + Micro-Frontend Architecture")
        )


global_planner_parser = PlannerOutputParser()
