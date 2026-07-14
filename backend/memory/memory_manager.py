from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from concurrent.futures import ThreadPoolExecutor

from backend.config import CONVERSATION_HISTORY_TURNS

from backend.memory.conversation_memory import ConversationMemory
from backend.memory.project_memory import ProjectMemory
from backend.memory.vector_memory import VectorMemory


@dataclass
class SessionContext:
    session_id: str
    history: list[dict[str, Any]]
    project: dict[str, Any]
    relevant_memory: list[dict[str, Any]]
    last_message: dict[str, Any] | None


class MemoryManager:

    def __init__(self):
        self.conversation_memory = ConversationMemory()
        self.project_memory = ProjectMemory()
        self.vector_memory = VectorMemory()

    def load_session(self, session_id: str, prompt: str = "") -> SessionContext:
        with ThreadPoolExecutor(max_workers=3) as executor:
            history_future = executor.submit(self.conversation_memory.get_history, session_id, CONVERSATION_HISTORY_TURNS)
            project_future = executor.submit(self.project_memory.load_project, session_id)
            relevant_future = executor.submit(self.vector_memory.search, session_id, prompt, 2) if prompt else None

            history = history_future.result()
            project = project_future.result()
            relevant_memory = relevant_future.result() if relevant_future is not None else []

        last_message = self.conversation_memory.last_message(session_id)

        return SessionContext(
            session_id=session_id,
            history=history,
            project=project,
            relevant_memory=relevant_memory,
            last_message=last_message,
        )

    def format_history(self, history: list[dict[str, Any]]) -> str:
        if not history:
            return "No previous conversation history."

        lines = []
        for item in history[-CONVERSATION_HISTORY_TURNS:]:
            lines.append(
                f"- User: {item.get('user_prompt', '')}\n"
                f"  AI: {item.get('ai_response', '')}\n"
                f"  Agent: {item.get('agent_name', '')} | Route: {item.get('route', '')} | Time: {item.get('timestamp', '')}"
            )

        return "\n".join(lines)

    def format_project(self, project: dict[str, Any]) -> str:
        frontend = ", ".join(project.get("frontend_stack", [])) or "Not set"
        backend = ", ".join(project.get("backend_stack", [])) or "Not set"
        completed = ", ".join(project.get("completed_tasks", [])) or "None"
        pending = ", ".join(project.get("pending_tasks", [])) or "None"
        files = ", ".join(project.get("generated_files", [])) or "None"

        return f"""Current Project: {project.get('current_project', 'Not set')}
Frontend Stack: {frontend}
Backend Stack: {backend}
Database: {project.get('database', 'Not set')}
Completed Tasks: {completed}
Pending Tasks: {pending}
Generated Files: {files}
Last Agent: {project.get('last_agent', 'None')}
Last Task: {project.get('last_task', 'None')}"""

    def format_relevant_memory(self, relevant_memory: list[dict[str, Any]]) -> str:
        if not relevant_memory:
            return "No relevant memory found."

        lines = []
        for item in relevant_memory:
            lines.append(f"- {item.get('text', '')} (score: {item.get('score', 0)})")

        return "\n".join(lines)

    def format_compact_context(self, context: dict[str, Any]) -> str:
        return f"""Recent History
{context['history_text']}

Project Snapshot
{context['project_text']}

Relevant Memory
{context['relevant_text']}"""

    def build_context_block(self, session_id: str, prompt: str) -> dict[str, Any]:
        session = self.load_session(session_id, prompt=prompt)
        return {
            "session_id": session.session_id,
            "history": session.history,
            "project": session.project,
            "relevant_memory": session.relevant_memory,
            "last_message": session.last_message,
            "history_text": self.format_history(session.history),
            "project_text": self.format_project(session.project),
            "relevant_text": self.format_relevant_memory(session.relevant_memory),
        }

    def build_context_bundle(self, session_id: str, prompt: str) -> tuple[dict[str, Any], str]:
        context = self.build_context_block(session_id, prompt)
        return context, self.format_compact_context(context)

    def build_planner_prompt(self, prompt: str, session_id: str) -> str:
        context = self.build_context_block(session_id, prompt)
        return f"""Current Prompt
{prompt}

Conversation History
{context['history_text']}

Project Status
{context['project_text']}

Relevant Memory
{context['relevant_text']}"""

    def build_router_prompt(self, prompt: str, session_id: str) -> str:
        context = self.build_context_block(session_id, prompt)
        return f"""Current Prompt
{prompt}

Previous Messages
{context['history_text']}

Current Project
{context['project_text']}

Relevant Memory
{context['relevant_text']}"""

    def build_agent_prompt(self, prompt: str, session_id: str, plan: str, architecture: str) -> str:
        context = self.build_context_block(session_id, prompt)
        return f"""Project Context
{context['project_text']}

Conversation History
{context['history_text']}

Relevant Memory
{context['relevant_text']}

Current Task
{prompt}

Planner Output
{plan}

Architect Output
{architecture}
"""

    def build_compact_memory_context(self, session_id: str, prompt: str) -> str:
        context = self.build_context_block(session_id, prompt)
        return self.format_compact_context(context)

    def save_interaction(
        self,
        session_id: str,
        user_prompt: str,
        ai_response: str,
        agent_name: str,
        route: str,
        plan: str = "",
        architecture: str = "",
    ) -> dict[str, Any]:
        self.vector_memory.add_text(session_id, user_prompt, {"type": "user_prompt", "agent_name": agent_name, "route": route})
        self.vector_memory.add_text(session_id, ai_response, {"type": "ai_response", "agent_name": agent_name, "route": route})

        self.conversation_memory.save_message(
            session_id=session_id,
            user_prompt=user_prompt,
            ai_response=ai_response,
            agent_name=agent_name,
            route=route,
            metadata={"plan": plan, "architecture": architecture},
        )

        project = self.project_memory.load_project(session_id)
        project["last_task"] = user_prompt
        project["last_agent"] = agent_name

        if plan:
            project["latest_plan"] = plan

        if architecture:
            project["latest_architecture"] = architecture

        if user_prompt and user_prompt not in project["completed_tasks"]:
            project["completed_tasks"].append(user_prompt)

        if agent_name and agent_name not in ["planner", "architect"]:
            generated_marker = f"{agent_name}:{user_prompt[:40]}"
            if generated_marker not in project["generated_files"]:
                project["generated_files"].append(generated_marker)

        if not project.get("current_project"):
            project["current_project"] = user_prompt

        return self.project_memory.save_project(session_id, project)

    def get_history(self, session_id: str, limit: int | None = None):
        return self.conversation_memory.get_history(session_id, limit=limit)

    def get_project(self, session_id: str):
        return self.project_memory.load_project(session_id)

    def clear_session(self, session_id: str):
        self.conversation_memory.clear_history(session_id)
        self.project_memory.clear_project(session_id)
        self.vector_memory.clear(session_id)


memory_manager = MemoryManager()
