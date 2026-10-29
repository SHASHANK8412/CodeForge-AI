"""
AIForge Universal Command Center — Intent Routing & Context Resolution
======================================================================
Interprets natural language queries entered into the Command Palette (Ctrl+K),
determines intent (Agent, Project, Memory, Tool, Chat, Direct Action),
retrieves smart context, and builds actionable execution payloads.
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.memory.ai_memory_service import global_ai_memory_service, MemoryCategory, MemoryImportance, MemoryScope

_logger = logging.getLogger("aiforge.command_center.router")


class CommandIntentType(str):
    AGENT_CODING = "AGENT_CODING"
    AGENT_STUDY = "AGENT_STUDY"
    AGENT_RESEARCH = "AGENT_RESEARCH"
    AGENT_RESUME = "AGENT_RESUME"
    AGENT_DATA = "AGENT_DATA"
    AGENT_CREATIVE = "AGENT_CREATIVE"
    PROJECT_ACTION = "PROJECT_ACTION"
    MEMORY_STORE = "MEMORY_STORE"
    MEMORY_SEARCH = "MEMORY_SEARCH"
    TOOL_WORKSPACE = "TOOL_WORKSPACE"
    TOOL_SECURITY = "TOOL_SECURITY"
    SAVED_OUTPUTS = "SAVED_OUTPUTS"
    NAVIGATION = "NAVIGATION"
    CHAT_PROMPT = "CHAT_PROMPT"


class CommandResolution(BaseModel):
    query: str
    intent: str
    confidence: float
    title: str
    description: str
    target_view: str  # e.g., "agents", "projects", "memory", "code", "chat", "saved"
    action_type: str  # "NAVIGATE", "LAUNCH_AGENT", "STORE_MEMORY", "SET_PROMPT"
    action_payload: Optional[Dict[str, Any]] = None
    suggested_chips: List[str] = Field(default_factory=list)
    recalled_memories: List[Dict[str, Any]] = Field(default_factory=list)


class UniversalCommandRouter:
    """
    Intelligent NLP intent resolver and context assembler for AIForge Command Palette.
    """

    def resolve_command(
        self,
        query: str,
        current_project_id: Optional[str] = None,
        current_view: Optional[str] = None
    ) -> CommandResolution:
        q = query.strip().lower()
        if not q:
            return self._default_empty_resolution(current_project_id)

        # 1. Check for explicit Memory Storage intent (e.g. "remember that...", "save preference...", "always use...")
        mem_store_match = re.search(r"^(?:remember(?:\s+that)?|save(?:\s+preference)?|always use|never use)\s+(.+)", q, re.I)
        if mem_store_match:
            fact = mem_store_match.group(1).strip()
            return CommandResolution(
                query=query,
                intent=CommandIntentType.MEMORY_STORE,
                confidence=0.98,
                title=f"Save to AI Memory: '{fact[:50]}'",
                description="Immediately store this preference into AIForge persistent memory graph",
                target_view="memory",
                action_type="STORE_MEMORY",
                action_payload={"title": f"Preference: {fact[:40]}", "content": fact, "scope": "PERSONAL"},
                suggested_chips=["View All Memories", "Personal Preferences", "Project Context"]
            )

        # 2. Check for Study / Exam / Syllabus intent (e.g. "create study plan...", "quiz for dbms...", "learn os...")
        if any(w in q for w in ["study", "exam", "quiz", "syllabus", "notes", "dbms", "course", "learn "]):
            recall = global_ai_memory_service.smart_recall(user_prompt=query, project_id=current_project_id, limit=3)
            return CommandResolution(
                query=query,
                intent=CommandIntentType.AGENT_STUDY,
                confidence=0.95,
                title="Launch Study & Exam Agent",
                description=f"Deconstruct syllabus, generate multi-day milestones, notes, and quiz for: '{query}'",
                target_view="agents",
                action_type="LAUNCH_AGENT",
                action_payload={"agent_id": "agent-study", "goal": query},
                recalled_memories=recall.get("recalled_memories", []),
                suggested_chips=["5-Day Mastery Plan", "Interactive Diagnostic Quiz", "High-Yield Summary"]
            )

        # 3. Check for Coding / Debug / Fix intent
        if any(w in q for w in ["code", "debug", "refactor", "build app", "fastapi", "react", "fix error", "stacktrace", "python", "javascript"]):
            recall = global_ai_memory_service.smart_recall(user_prompt=query, project_id=current_project_id, limit=3)
            return CommandResolution(
                query=query,
                intent=CommandIntentType.AGENT_CODING,
                confidence=0.96,
                title="Launch Autonomous Coding Agent",
                description=f"Plan architecture, generate clean code, run unit tests, and verify: '{query}'",
                target_view="agents",
                action_type="LAUNCH_AGENT",
                action_payload={"agent_id": "agent-coding", "goal": query, "project_id": current_project_id},
                recalled_memories=recall.get("recalled_memories", []),
                suggested_chips=["Open Monaco IDE", "Run SAST Vulnerability Scan", "Auto-Repair"]
            )

        # 4. Check for Research / Comparison intent
        if any(w in q for w in ["research", "compare", "benchmark", "rfc", "trade-off", "vs ", "explore", "survey"]):
            recall = global_ai_memory_service.smart_recall(user_prompt=query, project_id=current_project_id, limit=3)
            return CommandResolution(
                query=query,
                intent=CommandIntentType.AGENT_RESEARCH,
                confidence=0.94,
                title="Launch Deep Research Agent",
                description=f"Perform library search, gather technical specifications, and synthesize RFC for: '{query}'",
                target_view="agents",
                action_type="LAUNCH_AGENT",
                action_payload={"agent_id": "agent-research", "goal": query},
                recalled_memories=recall.get("recalled_memories", []),
                suggested_chips=["Synthesize RFC Document", "Benchmark Latency vs Throughput"]
            )

        # 5. Check for Resume / Career intent
        if any(w in q for w in ["resume", "cv", "job", "interview", "ats", "career", "linkedin"]):
            return CommandResolution(
                query=query,
                intent=CommandIntentType.AGENT_RESUME,
                confidence=0.95,
                title="Launch Resume & Career Agent",
                description=f"Scan ATS keyword gaps, rewrite STAR accomplishments, and generate mock questions for: '{query}'",
                target_view="agents",
                action_type="LAUNCH_AGENT",
                action_payload={"agent_id": "agent-resume", "goal": query},
                suggested_chips=["Optimize ATS Score", "Generate STAR Bullet Points", "Mock Interview Questions"]
            )

        # 6. Check for Data Analyst intent
        if any(w in q for w in ["data", "analyze", "dataset", "stats", "churn", "retention", "chart", "metrics", "sql"]):
            return CommandResolution(
                query=query,
                intent=CommandIntentType.AGENT_DATA,
                confidence=0.93,
                title="Launch Data Analyst Agent",
                description=f"Run statistical regressions, generate chart specifications, and extract insights for: '{query}'",
                target_view="agents",
                action_type="LAUNCH_AGENT",
                action_payload={"agent_id": "agent-data-analyst", "goal": query},
                suggested_chips=["Cohort Retention Curve", "SQL Query Generator", "Executive Insights"]
            )

        # 7. Check for Project Continuation / Open Project intent
        if any(w in q for w in ["continue", "project", "my work", "fooddelivery", "workspace", "yesterday"]):
            proj = current_project_id or "aiforge-fooddelivery-ai"
            recall = global_ai_memory_service.smart_recall(user_prompt=query, project_id=proj, limit=4)
            return CommandResolution(
                query=query,
                intent=CommandIntentType.PROJECT_ACTION,
                confidence=0.91,
                title=f"Continue Active Project: {proj}",
                description=f"Resume workspace with {recall.get('total_recalled', 0)} active memories synchronized",
                target_view="projects",
                action_type="NAVIGATE",
                action_payload={"project_id": proj},
                recalled_memories=recall.get("recalled_memories", []),
                suggested_chips=["Open Code Workspace", "Project X-Ray", "Agent Timeline"]
            )

        # 8. Check for Saved Outputs / Snippets intent
        if any(w in q for w in ["saved", "bookmarks", "snippets", "history", "outputs", "exports"]):
            return CommandResolution(
                query=query,
                intent=CommandIntentType.SAVED_OUTPUTS,
                confidence=0.90,
                title="Open Saved AI Outputs & Library",
                description="Browse persisted snippets, architecture RFCs, and exported code modules",
                target_view="saved",
                action_type="NAVIGATE",
                action_payload={},
                suggested_chips=["Filter by Coding", "Export All Outputs", "Recent Activity Log"]
            )

        # Fallback to General AI Chat Prompt with Smart Recall
        recall = global_ai_memory_service.smart_recall(user_prompt=query, project_id=current_project_id, limit=3)
        return CommandResolution(
            query=query,
            intent=CommandIntentType.CHAT_PROMPT,
            confidence=0.85,
            title=f"Ask AIForge: '{query[:50]}'",
            description="Send prompt to AI Assistant with automatic Smart Memory Recall context",
            target_view="chat",
            action_type="SET_PROMPT",
            action_payload={"prompt": query, "memory_active": True},
            recalled_memories=recall.get("recalled_memories", []),
            suggested_chips=["Plan Generator Mode", "Document Grounding (RAG)", "Autonomous Agents"]
        )

    def _default_empty_resolution(self, project_id: Optional[str]) -> CommandResolution:
        proj = project_id or "aiforge-fooddelivery-ai"
        return CommandResolution(
            query="",
            intent="INITIAL_SUGGESTIONS",
            confidence=1.0,
            title="AIForge Universal Command Center",
            description="Type natural language instructions or select a ready-made quick action",
            target_view="dashboard",
            action_type="NAVIGATE",
            suggested_chips=[
                "🤖 Run Agent", "💻 Code", "📚 Study", 
                "🔬 Research", "✍️ Write", "📊 Analyze", "🧠 Remember"
            ]
        )


global_command_router = UniversalCommandRouter()
