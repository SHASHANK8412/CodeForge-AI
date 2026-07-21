from typing import TypedDict
from time import perf_counter

from langgraph.graph import StateGraph, END

from backend.agents.planner_agent import PlannerAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.router_agent import RouterAgent
from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.memory.memory_manager import memory_manager
from backend.agents.testing_agent import TestingAgent
from backend.agents.frontend_agent import FrontendAgent
from backend.agents.deployment_agent import DeploymentAgent

class GraphState(TypedDict):
    session_id: str
    prompt: str
    memory_context: str
    history_text: str
    project_text: str
    collaboration_mode: bool
    plan: str
    architecture: str
    route: str
    agent_name: str
    generated_code: str
    reviewed_code: str
    explanation: str
    response: str
    execution_mode: str
    testing_report: str
    quality_score: str
    unit_tests: str
    edge_cases: str
    complexity: str


ARCHITECT_REQUIRED_SECTIONS = [
    "project architecture",
    "folder structure",
    "frontend files",
    "backend files",
    "database schema",
    "api routes",
    "dependencies",
]


planner = PlannerAgent()
architect = ArchitectAgent()
router = RouterAgent()
coding = CodingAgent()
debug = DebugAgent()
resume = ResumeAgent()
explanation = ExplanationAgent()
reviewer = ReviewerAgent()
testing_agent = TestingAgent()
frontend = FrontendAgent()
deployment = DeploymentAgent()


def log_stage(message: str):
    print(message)


def log_stage_duration(stage: str, started_at: float):
    elapsed_ms = (perf_counter() - started_at) * 1000
    print(f"{stage} Completed in {elapsed_ms:.1f}ms")


def classify_request(prompt: str, memory_context: str = "") -> tuple[str, str]:
    normalized = prompt.lower()
    memory_hint = (memory_context or "").lower()

    if any(phrase in normalized for phrase in ["continue", "proceed", "next", "resume where we left off"]):
        if any(word in memory_hint for word in ["resume", "debug", "error", "explain", "architecture", "rag", "document"]):
            if "resume" in memory_hint:
                return "resume", "fast"
            if "debug" in memory_hint or "error" in memory_hint:
                return "debug", "full"
            if "explain" in memory_hint or "architecture" in memory_hint:
                return "explanation", "fast"
            if "rag" in memory_hint or "document" in memory_hint:
                return "rag", "fast"

        return "coding", "full"

    if any(word in normalized for word in ["resume", "cv", "linkedin", "cover letter"]):
        return "resume", "fast"

    if any(word in normalized for word in ["explain", "what is", "why", "how does", "difference", "compare", "teach"]):
        return "explanation", "fast"

    if any(word in normalized for word in ["bug", "error", "fix", "traceback", "crash", "not working"]):
        return "debug", "full"

    project_keywords = ["build", "create", "design", "develop", "project", "app", "system", "portal", "dashboard"]
    if any(word in normalized for word in project_keywords):
        return "coding", "full"

    simple_code_hints = ["function", "script", "snippet", "algorithm", "method", "regex", "one-liner", "utility", "helper", "class"]
    project_scale_hints = ["api", "database", "docker", "microservice", "full stack", "fullstack", "endpoint", "schema", "react", "frontend", "backend", "deployment"]
    if any(hint in normalized for hint in simple_code_hints) and not any(hint in normalized for hint in project_scale_hints):
        return "coding", "fast"

    if len(normalized.split()) <= 6:
        return "explanation", "fast"

    return "coding", "full"


# ---------------- Memory Load ---------------- #

def load_memory_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Memory Loaded")

    session_id = state.get("session_id", "default")
    collaboration_mode = not hasattr(memory_manager, "build_context_bundle")
    if hasattr(memory_manager, "build_context_bundle"):
        context, memory_context = memory_manager.build_context_bundle(session_id, state["prompt"])
    else:
        context = memory_manager.build_context_block(session_id, state["prompt"])
        if hasattr(memory_manager, "format_compact_context"):
            memory_context = memory_manager.format_compact_context(context)
        else:
            memory_context = format_memory_context(context)

    log_stage_duration("Memory Loaded", started_at)

    return {
        "session_id": session_id,
        "prompt": state["prompt"],
        "memory_context": memory_context,
        "history_text": context["history_text"],
        "project_text": context["project_text"],
        "collaboration_mode": collaboration_mode,
        "execution_mode": state.get("execution_mode", "full"),
    }


# ---------------- Request Classification ---------------- #

def classify_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Request Classification Started")

    route, execution_mode = classify_request(state["prompt"], state.get("memory_context", ""))

    log_stage(f"Request Classified As {route.title()} ({execution_mode})")
    log_stage_duration("Request Classification", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "history_text": state.get("history_text", ""),
        "project_text": state.get("project_text", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "route": route,
        "execution_mode": execution_mode,
    }


def classify_selector(state: GraphState):

    if state.get("execution_mode") == "fast" and state.get("route") == "resume":
        return "resume"

    if state.get("execution_mode") == "fast" and state.get("route") == "explanation":
        return "explanation"

    return "full"


# ---------------- Planner ---------------- #

def planner_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Planner Started")

    planner_prompt = f"""Current Prompt
{state['prompt']}

{state.get('memory_context', '')}
"""
    plan = invoke_agent(planner, planner_prompt, state.get("memory_context", ""))

    log_stage("Planner Completed")
    log_stage_duration("Planner", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": plan,
    }


# ---------------- Architect ---------------- #

def _summarize_plan_fallback(plan: str) -> str:
    from backend.graph.parallel_workflow import summarize_plan
    return summarize_plan(plan)


def architect_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Architect Started")

    summarized_plan = _summarize_plan_fallback(state['plan'])
    architecture_input = f"""Planner Output Summary
{summarized_plan}"""
    architecture = invoke_agent(architect, architecture_input, state.get("memory_context", ""))

    log_stage("Architect Completed")
    log_stage_duration("Architect", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state["plan"],
        "architecture": architecture,
    }


# ---------------- Architecture Validation ---------------- #

def validate_architecture_sections(architecture: str):

    normalized = architecture.lower()
    missing = [
        section
        for section in ARCHITECT_REQUIRED_SECTIONS
        if section not in normalized
    ]

    return len(missing) == 0, missing


def enforce_architecture_sections(architecture: str):

    is_complete, missing = validate_architecture_sections(architecture)

    if is_complete:
        return architecture

    missing_lines = "\n".join([f"- {section.title()}" for section in missing])

    return f"""{architecture}

## Architecture Quality Check

Status: Incomplete

Missing Required Sections:
{missing_lines}

Please revise the architecture before implementation begins.
"""


def architecture_validator_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Architecture Validator Started")

    architecture = enforce_architecture_sections(state["architecture"])

    log_stage("Architecture Validator Completed")
    log_stage_duration("Architecture Validator", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state["plan"],
        "architecture": architecture,
    }


# ---------------- Router ---------------- #

def router_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Router Started")

    route = invoke_router(router, state["prompt"], state.get("memory_context", ""))

    log_stage(f"Router Selected {route.title()}Agent")
    log_stage_duration("Router", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": route,
        "execution_mode": state.get("execution_mode", "full"),
    }


# ---------------- Shared Context ---------------- #

def build_enhanced_prompt(state: GraphState) -> str:

    return f"""
Memory Context

{state.get('memory_context', '')}

Project Plan

{state['plan']}

Software Architecture

{state['architecture']}

User Request

{state['prompt']}
"""


def build_agent_context(state: GraphState, previous_output: str = "") -> str:

    return f"""Project Context
{state.get('memory_context', '')}

Conversation History
{state.get('history_text', '')}

Planner Output
{state.get('plan', '')}

Architect Output
{state.get('architecture', '')}

Previous Agent Output
{previous_output}

Current Task
{state['prompt']}"""


def format_memory_context(context: dict) -> str:

    return f"""Recent History
{context.get('history_text', '')}

Project Snapshot
{context.get('project_text', '')}

Relevant Memory
{context.get('relevant_text', '')}"""


def invoke_agent(agent, user_prompt: str, memory_context: str = "", previous_output: str = ""):

    try:
        return agent.run(user_prompt, memory_context, previous_output)
    except TypeError:
        try:
            return agent.run(user_prompt, memory_context)
        except TypeError:
            return agent.run(user_prompt)


def invoke_router(router_agent, user_prompt: str, memory_context: str = ""):

    try:
        return router_agent.route(user_prompt, memory_context)
    except TypeError:
        return router_agent.route(user_prompt)


# ---------------- Agent Nodes ---------------- #

def coding_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Coding Started")

    from backend.utils.summarizer import extract_backend_info
    plan = state.get("plan", "")
    arch = state.get("architecture", "")
    backend_info = extract_backend_info(plan, arch)

    enhanced_prompt = build_agent_context(state, previous_output=backend_info)
    response = invoke_agent(coding, enhanced_prompt, state.get("memory_context", ""), backend_info)

    log_stage("Coding Completed")
    log_stage_duration("Coding", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "coding",
        "generated_code": response,
        "response": response,
    }

def frontend_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Frontend Started")

    from backend.utils.summarizer import extract_ui_info
    plan = state.get("plan", "")
    arch = state.get("architecture", "")
    plan_ui = extract_ui_info(plan, arch)

    enhanced_prompt = build_agent_context(
        state,
        previous_output=plan_ui
    )

    response = invoke_agent(
        frontend,
        enhanced_prompt,
        state.get("memory_context", ""),
        plan_ui
    )

    log_stage("Frontend Completed")
    log_stage_duration("Frontend", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "frontend",
        "generated_code": response,
        "response": response,
    }


def debug_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Debug Started")

    enhanced_prompt = build_agent_context(state, previous_output=state.get("architecture", ""))
    response = invoke_agent(debug, enhanced_prompt, state.get("memory_context", ""), state.get("plan", ""))

    log_stage("Debug Completed")
    log_stage_duration("Debug", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "debug",
        "generated_code": response,
        "response": response,
    }


def resume_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Resume Started")

    enhanced_prompt = build_agent_context(state, previous_output=state.get("architecture", ""))
    response = invoke_agent(resume, enhanced_prompt, state.get("memory_context", ""), state.get("plan", ""))

    log_stage("Resume Completed")
    log_stage_duration("Resume", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "resume"),
        "agent_name": "resume",
        "generated_code": response,
        "response": response,
    }


def explanation_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Explanation Started")

    previous_output = state.get("reviewed_code") or state.get("generated_code") or state.get("architecture", "")
    enhanced_prompt = build_agent_context(state, previous_output=previous_output)
    response = invoke_agent(explanation, enhanced_prompt, state.get("memory_context", ""), previous_output)

    log_stage("Explanation Completed")
    log_stage_duration("Explanation", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "explanation"),
        "agent_name": "explanation",
        "explanation": response,
        "response": response,
    }


def reviewer_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Reviewer Started")

    from backend.utils.summarizer import extract_file_list, summarize_architecture
    gen_code = state.get("generated_code", "")
    file_list = extract_file_list(gen_code, "", "")
    arch_summary = summarize_architecture(state.get("architecture", ""))

    structured_summary = f"""Generated File List:
{file_list}

Architecture Summary:
{arch_summary}

Test Results:
{state.get('testing_report', 'No test execution output.')}

Changed Files:
No post-generation file edits detected."""

    review_prompt = build_agent_context(state, previous_output=structured_summary)
    response = invoke_agent(reviewer, review_prompt, state.get("memory_context", ""), structured_summary)

    log_stage("Reviewer Completed")
    log_stage_duration("Reviewer", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "reviewer",
        "generated_code": state.get("generated_code", ""),
        "reviewed_code": response,
        "response": response,
    }


def save_memory_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Save Memory Started")

    session_id = state.get("session_id", "default")
    agent_name = state.get("agent_name", state.get("route", "coding"))
    
    reviewed_code = state.get("reviewed_code", "")
    testing_report = state.get("testing_report", "")
    explanation = state.get("explanation", "")
    
    if reviewed_code or testing_report or explanation:
        final_response = f"""
=== REVIEWED CODE ===

{reviewed_code}

=== TESTING REPORT ===

{testing_report}

=== EXPLANATION ===

{explanation}
"""
    else:
        final_response = state.get("response") or state.get("generated_code") or ""

    memory_manager.save_interaction(
        session_id=session_id,
        user_prompt=state["prompt"],
        ai_response=final_response,
        agent_name=agent_name,
        route=state.get("route", "coding"),
        plan=state.get("plan", ""),
        architecture=state.get("architecture", ""),
    )

    log_stage("Workflow Finished")
    log_stage_duration("Save Memory", started_at)

    return {
        "session_id": session_id,
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "coding"),
        "agent_name": agent_name,
        "generated_code": state.get("generated_code", ""),
        "reviewed_code": reviewed_code,
        "explanation": explanation,
        "response": state.get("response", final_response),
    }


def route_selector(state: GraphState):

    route = state.get("route", "coding")

    if route == "frontend":
        return "frontend"

    if route == "debug":
        return "debug"

    if route == "resume":
        return "resume"

    if route == "explanation":
        return "explanation"

    return "coding"


def post_generation_selector(state: GraphState):

    if not hasattr(memory_manager, "format_compact_context"):
        return "reviewer"

    if state.get("execution_mode") == "fast":
        return "save_memory"

    return "reviewer"


def resume_post_selector(state: GraphState):

    if not hasattr(memory_manager, "format_compact_context"):
        return "explanation"

    if state.get("execution_mode") == "fast":
        return "save_memory"

    return "explanation"


# ---------------- Testing ---------------- #

def testing_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Testing Started")

    code = state.get("reviewed_code") or state.get("generated_code", "")

    report = testing_agent.process(code)

    log_stage("Testing Completed")
    log_stage_duration("Testing", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "history_text": state.get("history_text", ""),
        "project_text": state.get("project_text", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "coding"),
        "agent_name": "testing",
        "generated_code": state.get("generated_code", ""),
        "reviewed_code": state.get("reviewed_code", ""),
        "testing_report": report,
        "response": report,
    }


def deployment_node(state: GraphState):

    started_at = perf_counter()
    log_stage("Deployment Started")

    result_state = deployment.run(dict(state))

    log_stage("Deployment Completed")
    log_stage_duration("Deployment", started_at)

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "history_text": state.get("history_text", ""),
        "project_text": state.get("project_text", ""),
        "collaboration_mode": state.get("collaboration_mode", False),
        "execution_mode": state.get("execution_mode", "full"),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "coding"),
        "agent_name": "deployment",
        "generated_code": state.get("generated_code", ""),
        "reviewed_code": state.get("reviewed_code", ""),
        "testing_report": state.get("testing_report", ""),
        "deployment_files": result_state.get("deployment_files", {}),
        "deployment_report": result_state.get("deployment_report", {}),
        "deployment_platform": result_state.get("deployment_platform", "Unknown"),
        "deployment_guide": result_state.get("deployment_guide", ""),
        "response": result_state.get("deployment_guide", ""),
    }


# ---------------- Graph ---------------- #

builder = StateGraph(GraphState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("classify", classify_node)
builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("architecture_validator", architecture_validator_node)
builder.add_node("router", router_node)
builder.add_node("coding", coding_node)
builder.add_node("frontend", frontend_node)
builder.add_node("debug", debug_node)
builder.add_node("resume", resume_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("testing", testing_node)
builder.add_node("deployment", deployment_node)
builder.add_node("explanation", explanation_node)
builder.add_node("save_memory", save_memory_node)
builder.set_entry_point("load_memory")

builder.add_edge("load_memory", "classify")
builder.add_conditional_edges(
    "classify",
    classify_selector,
    {
        "full": "planner",
        "resume": "resume",
        "explanation": "explanation",
    },
)
builder.add_edge("planner", "architect")
builder.add_edge("architect", "architecture_validator")
builder.add_edge("architecture_validator", "router")
builder.add_conditional_edges(
    "router",
    route_selector,
    {
        "coding": "coding",
        "frontend": "frontend",
        "debug": "debug",
        "resume": "resume",
        "explanation": "explanation",
    }
)
builder.add_conditional_edges(
    "coding",
    post_generation_selector,
    {
        "reviewer": "reviewer",
        "save_memory": "save_memory",
    }
)
builder.add_conditional_edges(
    "frontend",
    post_generation_selector,
    {
        "reviewer": "reviewer",
        "save_memory": "save_memory",
    }
)
builder.add_conditional_edges(
    "debug",
    post_generation_selector,
    {
        "reviewer": "reviewer",
        "save_memory": "save_memory",
    }
)
builder.add_conditional_edges(
    "resume",
    resume_post_selector,
    {
        "explanation": "explanation",
        "save_memory": "save_memory",
    }
)
builder.add_edge("reviewer", "testing")
builder.add_edge("testing", "deployment")
builder.add_edge("deployment", "explanation")
builder.add_edge("explanation", "save_memory")
builder.add_edge("save_memory", END)

graph = builder.compile()