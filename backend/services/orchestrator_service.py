"""
AIForge Central AI Context & Multi-Agent Orchestration Engine
=============================================================
Unifies Context Resolution and Multi-Agent Delegation Chains:
1. ContextEngine: Combines User Intent + Active Project + Smart Recall Memories + Canvas State + Task State into a compact, prioritized prompt context.
2. MultiAgentOrchestrator: Coordinates multi-agent collaboration pipelines:
   Example: Research Agent -> Analyst Agent -> Planning Agent -> Coding Agent -> Reviewer Agent
   Includes shared execution state, tool permissions, step limits, and human approval gates.
"""

import time
import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.memory.ai_memory_service import global_ai_memory_service
from backend.agents.agent_mode_service import global_agent_mode_service, AgentStep, StepPhase, StepStatus, TaskStatus

_logger = logging.getLogger("aiforge.orchestration.engine")


class OrchestrationPipelineRequest(BaseModel):
    pipeline_id: str = Field(default_factory=lambda: f"pipe_{uuid.uuid4().hex[:8]}")
    title: str
    goal: str
    agents_sequence: List[str] = Field(default_factory=lambda: ["agent-research", "agent-data-analyst", "agent-coding"])
    project_id: Optional[str] = "aiforge-fooddelivery-ai"
    requires_human_approval: bool = True
    memory_enabled: bool = True


class OrchestrationStepResult(BaseModel):
    agent_id: str
    agent_name: str
    phase: str
    status: str
    output: str
    artifacts_created: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class OrchestrationPipelineRun(BaseModel):
    pipeline_id: str
    title: str
    goal: str
    status: str = "RUNNING"  # RUNNING, WAITING_APPROVAL, COMPLETED, FAILED, STOPPED
    progress_percent: int = 0
    current_agent_index: int = 0
    agents_sequence: List[str]
    steps_results: List[OrchestrationStepResult] = Field(default_factory=list)
    pending_approval_agent: Optional[str] = None
    final_synthesis: Optional[str] = None
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class AIContextEngine:
    """
    Central context resolver that builds lean, highly relevant contextual prompts.
    """

    def assemble_prompt_context(
        self,
        user_prompt: str,
        project_id: Optional[str] = None,
        canvas_state: Optional[Dict[str, Any]] = None,
        max_memories: int = 4
    ) -> Dict[str, Any]:
        # 1. Smart Memory Recall
        memory_result = global_ai_memory_service.smart_recall(
            user_prompt=user_prompt,
            project_id=project_id,
            limit=max_memories
        )

        context_blocks = []

        if memory_result.get("recalled_memories"):
            context_blocks.append("### Active AI Memory Context:")
            for m in memory_result["recalled_memories"]:
                context_blocks.append(f"- **[{m.get('scope', 'GLOBAL')}] {m.get('title')}**: {m.get('content')}")

        if project_id:
            context_blocks.append(f"### Target Project: `{project_id}`")

        if canvas_state and canvas_state.get("title"):
            context_blocks.append(f"### Active Canvas: `{canvas_state.get('title')}` (Type: {canvas_state.get('canvas_type')})")
            if isinstance(canvas_state.get("content"), str) and len(canvas_state["content"]) < 800:
                context_blocks.append(f"```text\n{canvas_state['content']}\n```")

        assembled_prompt = "\n\n".join(context_blocks) + f"\n\n### User Goal / Prompt:\n{user_prompt}"

        return {
            "assembled_prompt": assembled_prompt,
            "recalled_memories": memory_result.get("recalled_memories", []),
            "memory_active": len(memory_result.get("recalled_memories", [])) > 0,
            "project_id": project_id
        }


class MultiAgentOrchestrator:
    """
    Coordinates collaborative pipelines across multiple specialized agents.
    """

    def __init__(self):
        self._runs: Dict[str, OrchestrationPipelineRun] = {}
        self._seed_demo_run()

    def _seed_demo_run(self):
        demo = OrchestrationPipelineRun(
            pipeline_id="pipe_demo_competitor_plan",
            title="Competitor Tech Analysis & Implementation Blueprint",
            goal="Research food delivery microservices architectures and build a high-throughput order dispatch service",
            status="COMPLETED",
            progress_percent=100,
            current_agent_index=3,
            agents_sequence=["agent-research", "agent-data-analyst", "agent-coding"],
            steps_results=[
                OrchestrationStepResult(
                    agent_id="agent-research",
                    agent_name="Deep Research Agent",
                    phase="RESEARCH_SPECS",
                    status="COMPLETED",
                    output="Benchmarked Kafka vs Redis Streams for driver dispatching. Selected Redis Streams for <5ms P99 latency and low memory footprint.",
                    artifacts_created=["spec_benchmark.md"],
                    duration_seconds=2.4
                ),
                OrchestrationStepResult(
                    agent_id="agent-data-analyst",
                    agent_name="Data Analyst Agent",
                    phase="LOAD_ANALYSIS",
                    status="COMPLETED",
                    output="Analyzed peak dinner cohort throughput (15,000 orders/sec). Calculated connection pool sizes and Redis partition counts.",
                    artifacts_created=["throughput_model.json"],
                    duration_seconds=1.9
                ),
                OrchestrationStepResult(
                    agent_id="agent-coding",
                    agent_name="Coding Agent",
                    phase="CODE_GENERATION",
                    status="COMPLETED",
                    output="Generated FastAPI asynchronous dispatch worker with RS256 JWT auth, redis-py consumer groups, and comprehensive pytest suite.",
                    artifacts_created=["main.py", "worker.py", "test_worker.py"],
                    duration_seconds=3.2
                )
            ],
            final_synthesis="""# 🚀 Multi-Agent Orchestration Report: Order Dispatch Architecture

## 📋 Cross-Agent Collaboration Summary
1. **🔬 Research Agent**: Benchmarked Redis Streams (<5ms latency) vs Kafka for driver matching.
2. **📈 Data Analyst Agent**: Simulated 15,000 orders/sec peak load and computed worker partition shards.
3. **💻 Coding Agent**: Implemented production FastAPI worker with RS256 JWT authentication and automated test suite.

## ✅ Verification Status: 100% Pass (0 SAST Vulnerabilities)"""
        )
        self._runs[demo.pipeline_id] = demo

    def list_pipelines(self) -> List[OrchestrationPipelineRun]:
        return list(self._runs.values())

    def get_pipeline(self, pipeline_id: str) -> Optional[OrchestrationPipelineRun]:
        return self._runs.get(pipeline_id)

    def launch_pipeline(self, req: OrchestrationPipelineRequest) -> OrchestrationPipelineRun:
        run = OrchestrationPipelineRun(
            pipeline_id=req.pipeline_id,
            title=req.title,
            goal=req.goal,
            status="RUNNING",
            progress_percent=10,
            current_agent_index=0,
            agents_sequence=req.agents_sequence
        )
        self._runs[run.pipeline_id] = run
        return run


global_context_engine = AIContextEngine()
global_orchestrator = MultiAgentOrchestrator()
