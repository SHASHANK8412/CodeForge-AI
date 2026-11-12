"""
AIForge AI Core — agent runtime behind the AI Chat agent modes.

A run recalls the user's own memories, searches the user's own uploaded documents, and asks the local
model (backend.ai_core.model_provider). Every recorded step is something that actually happened, with
its measured duration; a model failure is recorded as a FAILED run, never answered with invented text.
Runs belong to the user who started them.
"""

import json
import logging
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.ai_core.agent_memory import global_memory_manager
from backend.ai_core.model_provider import LLMUnavailableError, global_model_provider
from backend.ai_core.rag_engine import global_rag_engine

_logger = logging.getLogger("aiforge.ai_core.runtime")


class AgentMode(str, Enum):
    CHAT = "CHAT"
    RESEARCH = "RESEARCH"
    ANALYZE = "ANALYZE"
    CODE = "CODE"
    AGENT = "AGENT"


MODE_INSTRUCTIONS = {
    AgentMode.CHAT: "Answer conversationally and concisely.",
    AgentMode.RESEARCH: "Explain the topic thoroughly, compare options and state trade-offs. Say when you are unsure.",
    AgentMode.ANALYZE: "Analyse the input step by step and give a clear conclusion.",
    AgentMode.CODE: "Write correct, complete code with a short explanation. Use fenced code blocks.",
    AgentMode.AGENT: "Work out what the user needs, plan the steps, and give a complete, practical answer.",
}


class ExecutionStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"stp_{uuid.uuid4().hex[:6]}")
    title: str
    stage: str  # "UNDERSTAND", "RETRIEVE", "RESPONSE"
    status: str = "COMPLETED"  # "COMPLETED", "FAILED"
    tool_used: Optional[str] = None
    output_summary: Optional[str] = None
    duration_seconds: float = 0.0


class AgentRunRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:8]}")
    user_id: str
    project_id: Optional[str] = None
    mode: AgentMode = AgentMode.AGENT
    prompt: str
    status: str = "COMPLETED"  # "COMPLETED", "FAILED"
    model_id: str = "auto"
    response_text: str = ""
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)      # e.g. a retrieved document that tried to give instructions
    steps: List[ExecutionStep] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class AgentRuntime:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).resolve().parent.parent / "data" / "agent_runs"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "runs.json"
        self._runs: Dict[str, AgentRunRecord] = {}
        self._load()

    def _load(self):
        if not self.storage_file.exists():
            return
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    if not item.get("user_id") or item.get("user_id") == "user_default":
                        continue          # demo and unowned runs from earlier versions belong to nobody
                    try:
                        r = AgentRunRecord(**item)
                    except Exception:
                        continue          # records in an older format are skipped, not guessed
                    self._runs[r.id] = r
        except Exception as e:
            _logger.error(f"Error loading agent runs: {e}")

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([r.model_dump() for r in self._runs.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving agent runs: {e}")

    def list_runs(self, user_id: str, project_id: Optional[str] = None) -> List[AgentRunRecord]:
        items = [r for r in self._runs.values() if r.user_id == user_id]
        if project_id:
            items = [r for r in items if r.project_id == project_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items

    def get_run(self, run_id: str, user_id: str) -> Optional[AgentRunRecord]:
        run = self._runs.get(run_id)
        return run if run is not None and run.user_id == user_id else None

    def execute_agent(
        self,
        prompt: str,
        user_id: str,
        mode: AgentMode = AgentMode.AGENT,
        model_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> AgentRunRecord:
        started = time.time()
        steps: List[ExecutionStep] = []

        t = time.time()
        memories = global_memory_manager.search(prompt, user_id=user_id, project_id=project_id, limit=3)
        steps.append(ExecutionStep(title=f"Recalled {len(memories)} saved memories", stage="UNDERSTAND",
                                   duration_seconds=round(time.time() - t, 3)))

        t = time.time()
        chunks = global_rag_engine.search(prompt, limit=3, project_id=project_id, user_id=user_id)
        citations = [{"source": c.filename, "ref": c.citation_ref, "snippet": c.text[:200]} for c in chunks]
        steps.append(ExecutionStep(title=f"Found {len(chunks)} matching passages in your documents", stage="RETRIEVE",
                                   tool_used="document_search" if chunks else None,
                                   duration_seconds=round(time.time() - t, 3)))

        system = ["You are AIForge, an AI software engineering assistant.", MODE_INSTRUCTIONS[mode]]
        if memories:
            system.append("Things the user asked you to remember:\n" + "\n".join(f"- {m.key}: {m.content}" for m in memories))
        # Document passages are untrusted data: they go in the user turn inside a delimited block, never in the system
        # prompt, and passages with instruction-like text are flagged to the model and reported to the user.
        from backend.security.untrusted_content import RULE, Passage, flagged_sources, warning_for, wrap_untrusted
        passages = [Passage(text=c.text, source=c.filename, label=c.citation_ref) for c in chunks]
        user_turn = prompt
        if passages:
            system.append(RULE + " Cite the documents you use by their id.")
            user_turn = wrap_untrusted(passages, purpose="the user's own documents") + "\n\nUser request:\n" + prompt
        warning = warning_for(flagged_sources(passages))

        run = AgentRunRecord(user_id=user_id, project_id=project_id, mode=mode, prompt=prompt,
                             warnings=[warning] if warning else [],
                             citations=citations, tools_used=["document_search"] if chunks else [])
        t = time.time()
        try:
            resp = global_model_provider.complete(
                [{"role": "system", "content": "\n\n".join(system)}, {"role": "user", "content": user_turn}],
                model_id=model_id,
            )
            run.response_text = resp.content
            run.model_id = resp.model_id
            steps.append(ExecutionStep(title="Model answered", stage="RESPONSE", duration_seconds=round(time.time() - t, 3)))
        except LLMUnavailableError as exc:
            run.status = "FAILED"
            run.error = f"The local model did not answer: {exc}"
            steps.append(ExecutionStep(title="Model call failed", stage="RESPONSE", status="FAILED",
                                       output_summary=str(exc), duration_seconds=round(time.time() - t, 3)))

        run.steps = steps
        run.duration_seconds = round(time.time() - started, 3)
        self._runs[run.id] = run
        self._save()
        return run


global_agent_runtime = AgentRuntime()
