import json
import logging
from typing import Dict, Any, Optional, List

from backend.memory.memory_manager import global_memory_manager
from backend.memory.retrieval import global_memory_retriever
from backend.memory.project_memory_service import global_project_memory_service
from backend.memory.codebase_indexer import global_codebase_indexer
from backend.memory.impact_analyzer import global_impact_analyzer

logger = logging.getLogger("aiforge.services.context_builder")


class AgentContextBuilder:
    """
    Centralized Context Builder that constructs tailored, role-specific context prompts
    for each specialized agent in the AIForge multi-agent system using:
    - Tier 1: Active Project Memories & Decisions (with conflict superseding)
    - Tier 2: Codebase Symbols, Relevant Files & Impact Analysis
    - Tier 3: Execution & Failure Fix Memory
    """

    def __init__(self, memory_service=None, indexer=None, impact_analyzer=None):
        self.memory_service = memory_service or global_project_memory_service
        self.indexer = indexer or global_codebase_indexer
        self.impact_analyzer = impact_analyzer or global_impact_analyzer

    def build_agent_context(
        self,
        project_id: str,
        generation_id: Optional[str] = None,
        agent_name: str = "generic",
        prompt: str = "",
        state: Optional[Dict[str, Any]] = None
    ) -> str:
        state = state or {}
        st_data = global_memory_manager.short_term.get_all()

        # 1. Tier 1: Retrieve ACTIVE non-superseded project memories
        active_memories = self.memory_service.get_active_memories(project_id)
        active_decisions = [m for m in active_memories if m.get("memory_type") in ("DECISION", "ARCHITECTURE_DECISION", "ARCHITECTURE")]

        # 2. Tier 2: Codebase Intelligence & Relevant Files Search
        relevant_code_files = self.indexer.search_codebase(project_id, prompt, top_k=6) if prompt else []
        impact_report = self.impact_analyzer.analyze_change_impact(project_id, targets=prompt, prompt=prompt) if prompt else None

        # 3. Tier 3: RAG & Failure Memories
        retrieved = global_memory_retriever.retrieve_relevant_memory(
            project_id=project_id,
            query=prompt or agent_name,
            agent_name=agent_name,
            generation_id=generation_id
        )
        rag_context = retrieved.get("rag_context", "")

        sections: List[str] = []
        agent_key = agent_name.lower()

        # Architecture and Tech stack memory summaries
        arch_memories = [m for m in active_memories if m.get("memory_type") in ("ARCHITECTURE", "TECHNOLOGY", "DATABASE", "API")]

        if "planner" in agent_key:
            sections.append(f"### Planner Goal & Objective\n{prompt}")
            if arch_memories:
                sections.append("### Established Project Architecture\n" + "\n".join([f"- **{m['key']}**: {m['value']}" for m in arch_memories[:6]]))
            if relevant_code_files:
                sections.append("### Existing Relevant Codebase Files\n" + "\n".join([f"- `{f['path']}` ({f['language']}): symbols={f.get('symbols', [])[:4]}" for f in relevant_code_files[:5]]))
            if impact_report and impact_report.affected_files:
                sections.append(f"### Change Impact Scope\n{impact_report.summary}\nAffected files: {impact_report.affected_files}")

        elif "architect" in agent_key:
            plan = state.get("plan") or st_data.get("agent_outputs", {}).get("planner") or {}
            sections.append(f"### Planner Requirements & Specs\n{json.dumps(plan, indent=2) if isinstance(plan, dict) else str(plan)}")
            if active_decisions:
                sections.append("### Active Architectural Decisions\n" + "\n".join([f"- {d['key']}: {d['value']}" for d in active_decisions[:6]]))
            if impact_report and impact_report.affected_routes:
                sections.append(f"### Existing API Routes to Preserve/Extend\n" + "\n".join([f"- {r}" for r in impact_report.affected_routes[:8]]))

        elif "frontend" in agent_key:
            arch = state.get("architecture") or st_data.get("agent_outputs", {}).get("architect") or {}
            plan = state.get("plan") or {}
            sections.append(f"### Target Architecture (Frontend Focus)\n{json.dumps(arch.get('components', arch), indent=2) if isinstance(arch, dict) else str(arch)}")
            if isinstance(plan, dict) and plan.get("functional_requirements"):
                sections.append("### UI Functional Requirements\n" + "\n".join([f"- {r}" for r in plan["functional_requirements"][:5]]))
            fe_files = [f for f in relevant_code_files if f.get("language") in ("javascript", "typescript") or "frontend" in f["path"]]
            if fe_files:
                sections.append("### Existing UI Components & State\n" + "\n".join([f"- `{f['path']}`: components={f.get('components', [])}" for f in fe_files[:4]]))

        elif "backend" in agent_key:
            arch = state.get("architecture") or st_data.get("agent_outputs", {}).get("architect") or {}
            db_schema = state.get("database") or st_data.get("agent_outputs", {}).get("database") or ""
            sections.append(f"### Target Architecture & API Specs\n{json.dumps(arch.get('routes', arch), indent=2) if isinstance(arch, dict) else str(arch)}")
            if db_schema:
                sections.append(f"### Database Schema Reference\n{str(db_schema)[:500]}")
            be_files = [f for f in relevant_code_files if f.get("language") == "python" or "backend" in f["path"]]
            if be_files:
                sections.append("### Existing Backend Services & Routes\n" + "\n".join([f"- `{f['path']}`: routes={[r.get('path') for r in f.get('routes', [])]}, models={f.get('models', [])}" for f in be_files[:4]]))

        elif "database" in agent_key:
            arch = state.get("architecture") or st_data.get("agent_outputs", {}).get("architect") or {}
            sections.append(f"### Entities & Data Models\n{json.dumps(arch.get('models', arch), indent=2) if isinstance(arch, dict) else str(arch)}")
            db_mem = [m for m in active_memories if m.get("memory_type") == "DATABASE"]
            if db_mem:
                sections.append("### Established Database Conventions\n" + "\n".join([f"- {m['key']}: {m['value']}" for m in db_mem]))

        elif "reviewer" in agent_key:
            fe = state.get("frontend", "")
            be = state.get("backend", "")
            db = state.get("database", "")
            sections.append(f"### Codebase to Review\nFrontend: {len(str(fe))} chars | Backend: {len(str(be))} chars | Database: {len(str(db))} chars")
            if active_decisions:
                sections.append("### Decisions & Conventions to Verify Against\n" + "\n".join([f"- {d['key']}: {d['value']}" for d in active_decisions[:6]]))

        elif "testing" in agent_key:
            be = state.get("backend", "")
            fe = state.get("frontend", "")
            sections.append(f"### Target System Source Code\nBackend:\n{str(be)[:600]}\n\nFrontend:\n{str(fe)[:400]}")
            if impact_report and impact_report.affected_tests:
                sections.append(f"### Recommended Test Target Suites\n" + "\n".join([f"- `{t}`" for t in impact_report.affected_tests]))

        elif "debug" in agent_key:
            test_results = state.get("test_results", {})
            sections.append(f"### Failure Diagnostics\nCategory: {test_results.get('failure_category', 'ERROR')}\nFailed Tests: {test_results.get('failed_tests', [])}")
            # Retrieve past fix memories
            past_fixes = global_project_memory_service.retrieve_relevant_memories(
                project_id=project_id,
                error_type=str(test_results.get("failure_category", "")),
                query_text=str(test_results.get("output", "")),
                top_k=2
            )
            if past_fixes:
                sections.append("### Previous Successful Fix Patterns\n" + "\n".join([f"- Root Cause: {pf.root_cause} | Fix: {pf.fix}" for pf in past_fixes if pf.fix]))

        else:
            sections.append(f"### Agent Task\n{prompt}")

        if rag_context:
            sections.append(f"### RAG Knowledge Base\n{rag_context[:600]}")

        full_context = "\n\n".join(sections)
        logger.info(f"[MEMORY] project={project_id} agent={agent_name} context_size={len(full_context)} chars (Memories={len(active_memories)}, Files={len(relevant_code_files)})")
        return full_context


# Singleton
global_agent_context_builder = AgentContextBuilder()


def build_agent_context(
    project_id: str,
    generation_id: Optional[str] = None,
    agent_name: str = "generic",
    prompt: str = "",
    state: Optional[Dict[str, Any]] = None
) -> str:
    return global_agent_context_builder.build_agent_context(
        project_id=project_id,
        generation_id=generation_id,
        agent_name=agent_name,
        prompt=prompt,
        state=state
    )

