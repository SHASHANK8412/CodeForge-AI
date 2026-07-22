"""
Day 43 - Conflict Detection Engine
===================================
Scans agent outputs across Frontend, Backend, Database, Documentation, and Testing for architectural conflicts.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class Conflict:
    id: str
    category: str  # api_mismatch, schema_mismatch, doc_mismatch, test_mismatch
    severity: str  # Low, Medium, High, Critical
    components: List[str]  # e.g. ["Frontend", "Backend"]
    description: str
    lhs_agent: str
    lhs_value: Any
    rhs_agent: str
    rhs_value: Any


class ConflictDetectionEngine:
    """Scans agent outputs and shared memory registries to identify inconsistencies."""

    def detect_conflicts(self, agent_outputs: Dict[str, Any], shared_memory: Any) -> List[Conflict]:
        conflicts: List[Conflict] = []

        frontend_out = agent_outputs.get("frontend", {})
        backend_out = agent_outputs.get("backend", {})
        database_out = agent_outputs.get("database", {})
        doc_out = agent_outputs.get("documentation", {})
        test_out = agent_outputs.get("testing", {})

        # 1. API Route Conflict Check (Backend vs Frontend)
        be_endpoints = backend_out.get("api_endpoints", [])
        fe_endpoints = frontend_out.get("api_calls", [])

        if be_endpoints and fe_endpoints:
            be_paths = {ep.get("path", "") for ep in be_endpoints if isinstance(ep, dict)}
            for fe_call in fe_endpoints:
                if isinstance(fe_call, dict):
                    fe_path = fe_call.get("path", "")
                    if fe_path and fe_path not in be_paths:
                        # Check if path differs only by prefix (e.g. /tasks vs /api/v1/tasks)
                        matching_be = [bp for bp in be_paths if fe_path.rstrip('/') in bp or bp.rstrip('/') in fe_path]
                        conflicts.append(Conflict(
                            id=f"conflict-api-{str(uuid.uuid4())[:6]}",
                            category="api_mismatch",
                            severity="High",
                            components=["Frontend", "Backend"],
                            description=f"Frontend calls '{fe_path}' but Backend endpoints are {list(be_paths)}",
                            lhs_agent="Frontend",
                            lhs_value=fe_path,
                            rhs_agent="Backend",
                            rhs_value=matching_be[0] if matching_be else list(be_paths)[0] if be_paths else ""
                        ))

        # 2. Schema Field Naming Conflict Check (Database vs Backend)
        db_tables = database_out.get("tables", [])
        be_models = backend_out.get("models", [])

        if db_tables and be_models:
            for db_t in db_tables:
                if isinstance(db_t, dict):
                    table_name = db_t.get("name", "").lower()
                    db_cols = set(db_t.get("columns", []))

                    for be_m in be_models:
                        if isinstance(be_m, dict):
                            model_name = be_m.get("name", "").lower()
                            if table_name in model_name or model_name in table_name:
                                be_fields = set(be_m.get("fields", []))
                                # Check for naming convention conflict (camelCase vs snake_case)
                                camel_fields = [f for f in be_fields if any(c.isupper() for c in f)]
                                if camel_fields and any("_" in col for col in db_cols):
                                    conflicts.append(Conflict(
                                        id=f"conflict-schema-{str(uuid.uuid4())[:6]}",
                                        category="schema_mismatch",
                                        severity="Medium",
                                        components=["Database", "Backend"],
                                        description=f"Database uses snake_case column names, but Backend model '{be_m.get('name')}' uses camelCase fields {camel_fields}",
                                        lhs_agent="Database",
                                        lhs_value="snake_case",
                                        rhs_agent="Backend",
                                        rhs_value="camelCase"
                                    ))

        # 3. Documentation API Route Mismatch Check
        doc_routes = doc_out.get("documented_routes", [])
        if be_endpoints and doc_routes:
            be_paths = {ep.get("path", "") for ep in be_endpoints if isinstance(ep, dict)}
            for dr in doc_routes:
                if dr not in be_paths:
                    conflicts.append(Conflict(
                        id=f"conflict-doc-{str(uuid.uuid4())[:6]}",
                        category="doc_mismatch",
                        severity="Low",
                        components=["Documentation", "Backend"],
                        description=f"Documentation references route '{dr}' which is missing from Backend implementation",
                        lhs_agent="Documentation",
                        lhs_value=dr,
                        rhs_agent="Backend",
                        rhs_value=list(be_paths)[0] if be_paths else ""
                    ))

        # 4. Testing Endpoint Assertion Check
        test_routes = test_out.get("tested_endpoints", [])
        if be_endpoints and test_routes:
            be_paths = {ep.get("path", "") for ep in be_endpoints if isinstance(ep, dict)}
            for tr in test_routes:
                if tr not in be_paths:
                    conflicts.append(Conflict(
                        id=f"conflict-test-{str(uuid.uuid4())[:6]}",
                        category="test_mismatch",
                        severity="High",
                        components=["Testing", "Backend"],
                        description=f"Test suite asserts endpoint '{tr}' which does not match Backend routes",
                        lhs_agent="Testing",
                        lhs_value=tr,
                        rhs_agent="Backend",
                        rhs_value=list(be_paths)[0] if be_paths else ""
                    ))

        return conflicts
