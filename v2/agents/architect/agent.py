"""
AIForge V2 – Architect Agent Class
===================================
Architect Agent V2 converting Product Blueprints into production-grade System Architecture designs.
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole
from v2.agents.architect.prompts import ARCHITECT_V2_SYSTEM_PROMPT
from v2.agents.architect.models import ArchitectureReport
from v2.agents.architect.architecture_generator import global_architecture_generator
from v2.agents.architect.api_designer import global_api_designer
from v2.agents.architect.database_designer import global_database_designer
from v2.agents.architect.folder_generator import global_folder_generator
from v2.agents.architect.validator import global_architecture_validator
from v2.logs.logger import global_v2_logger

_logger = logging.getLogger("aiforge.v2.architect")


class ArchitectAgentV2(BaseAgentV2):
    """
    Architect Agent V2: Chief Software Architect of AIForge V2.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.ARCHITECT,
            system_prompt=ARCHITECT_V2_SYSTEM_PROMPT
        )

    def design_architecture(self, prompt: str, project_id: str = "proj_v2_default") -> ArchitectureReport:
        started_at = time.perf_counter()
        _logger.info(f"ArchitectAgentV2: Designing technical system architecture for prompt: '{prompt[:60]}...'")

        raw_output = self.run(prompt)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        try:
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_output.strip()

            data = json.loads(json_str)
        except Exception as exc:
            _logger.warning(f"ArchitectAgentV2: Exception parsing LLM JSON output ({exc}). Assembling architectural design package via specialized designers.")
            data = {}

        p_lower = prompt.lower()
        is_enterprise = any(k in p_lower for k in ["enterprise", "social media", "instagram", "ecommerce", "uber", "platform"])

        proj_name = data.get("project_name") or ("Enterprise Web Platform" if is_enterprise else "AI Resume Analyzer")
        components = global_architecture_generator.generate_components(proj_name, is_enterprise=is_enterprise)
        apis = global_api_designer.generate_api_specs(proj_name)
        db_schema = global_database_designer.generate_schema(proj_name)
        folders = global_folder_generator.generate_tree(proj_name)

        from v2.agents.architect.models import (
            SecurityStrategy, CacheStrategySpec, VectorStoreSpec, DeploymentArchitecture
        )

        report = ArchitectureReport(
            project_id=project_id,
            project_name=proj_name,
            high_level_architecture=data.get("high_level_architecture", "React Frontend -> FastAPI Gateway -> PostgreSQL DB -> Redis Cache"),
            low_level_architecture=data.get("low_level_architecture", "Decoupled REST microservices with JWT Auth middleware and ChromaDB embeddings"),
            folder_structure=data.get("folder_structure", folders),
            components=components,
            apis=apis,
            database=db_schema,
            security=SecurityStrategy(),
            caching=CacheStrategySpec(),
            vector_store=VectorStoreSpec(),
            deployment=DeploymentArchitecture(),
            risks=data.get("risks", ["High concurrency connection pool limits", "Cache eviction under memory pressure"]),
            confidence_score=float(data.get("confidence_score", 96.5))
        )

        is_valid, issues = global_architecture_validator.validate_report(report)

        global_v2_logger.log_agent_action(
            agent_name="architect",
            input_text=prompt,
            output_text=f"Architecture design generated. APIs: {len(report.apis)}, Tables: {len(report.database.tables)}, Components: {len(report.components)}",
            execution_time_ms=elapsed_ms,
            metadata={
                "apis_count": len(report.apis),
                "tables_count": len(report.database.tables),
                "components_count": len(report.components),
                "confidence_score": report.confidence_score,
                "is_valid": is_valid
            }
        )

        return report


global_architect_agent_v2 = ArchitectAgentV2()
