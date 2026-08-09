import json
import logging
from typing import Dict, Any, Optional, List

from backend.memory.memory_manager import global_memory_manager
from backend.memory.retrieval import global_memory_retriever

logger = logging.getLogger("aiforge.services.context_builder")


class AgentContextBuilder:
    """
    Centralized Context Builder that constructs tailored, role-specific context prompts
    for each specialized agent in the AIForge multi-agent system.
    """

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

        # Retrieve relevant memories and decisions for this project
        retrieved = global_memory_retriever.retrieve_relevant_memory(
            project_id=project_id,
            query=prompt or agent_name,
            agent_name=agent_name,
            generation_id=generation_id
        )

        decisions = retrieved.get("decisions", [])
        memories = retrieved.get("memories", [])
        rag_context = retrieved.get("rag_context", "")

        sections: List[str] = []

        agent_key = agent_name.lower()

        if "planner" in agent_key:
            sections.append(f"### Planner Objective\n{prompt}")
            if memories:
                sections.append(f"### Project Historical Memory\n" + "\n".join([f"- {m['key']}: {m['value']}" for m in memories[:5]]))

        elif "architect" in agent_key:
            plan = state.get("plan") or st_data.get("agent_outputs", {}).get("planner") or {}
            sections.append(f"### Planner Requirements & Specs\n{json.dumps(plan, indent=2) if isinstance(plan, dict) else str(plan)}")
            if decisions:
                sections.append("### Established Decisions\n" + "\n".join([f"- {d['decision']} (Reason: {d['reason']})" for d in decisions]))

        elif "frontend" in agent_key:
            arch = state.get("architecture") or st_data.get("agent_outputs", {}).get("architect") or {}
            plan = state.get("plan") or {}
            sections.append(f"### Target Architecture (Frontend Focus)\n{json.dumps(arch.get('components', arch), indent=2) if isinstance(arch, dict) else str(arch)}")
            if isinstance(plan, dict) and plan.get("functional_requirements"):
                sections.append(f"### UI Functional Requirements\n" + "\n".join([f"- {r}" for r in plan["functional_requirements"][:5]]))
            if decisions:
                sections.append("### Architecture Decisions\n" + "\n".join([f"- {d['decision']}" for d in decisions if 'frontend' in d['decision'].lower() or 'ui' in d['decision'].lower()]))

        elif "backend" in agent_key:
            arch = state.get("architecture") or st_data.get("agent_outputs", {}).get("architect") or {}
            db_schema = state.get("database") or st_data.get("agent_outputs", {}).get("database") or ""
            sections.append(f"### Target Architecture & API Specs\n{json.dumps(arch.get('routes', arch), indent=2) if isinstance(arch, dict) else str(arch)}")
            if db_schema:
                sections.append(f"### Database Schema Reference\n{str(db_schema)[:500]}")

        elif "database" in agent_key:
            arch = state.get("architecture") or st_data.get("agent_outputs", {}).get("architect") or {}
            sections.append(f"### Entities & Data Models\n{json.dumps(arch.get('models', arch), indent=2) if isinstance(arch, dict) else str(arch)}")

        elif "reviewer" in agent_key:
            fe = state.get("frontend", "")
            be = state.get("backend", "")
            db = state.get("database", "")
            sections.append(f"### Codebase to Review\nFrontend: {len(str(fe))} chars | Backend: {len(str(be))} chars | Database: {len(str(db))} chars")
            if decisions:
                sections.append("### Decisions to Verify Against\n" + "\n".join([f"- {d['decision']}" for d in decisions]))

        elif "testing" in agent_key:
            be = state.get("backend", "")
            fe = state.get("frontend", "")
            sections.append(f"### Target System Source Code\nBackend:\n{str(be)[:600]}\n\nFrontend:\n{str(fe)[:400]}")

        else:
            sections.append(f"### Agent Task\n{prompt}")

        # Always attach RAG if present
        if rag_context:
            sections.append(f"### RAG Context\n{rag_context[:600]}")

        full_context = "\n\n".join(sections)
        logger.info(f"[MEMORY] project={project_id} agent={agent_name} context_size={len(full_context)} chars")
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
