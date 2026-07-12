from typing import TypedDict
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


class GraphState(TypedDict):
    session_id: str
    prompt: str
    memory_context: str
    history_text: str
    project_text: str
    plan: str
    architecture: str
    route: str
    agent_name: str
    generated_code: str
    reviewed_code: str
    explanation: str
    response: str


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


def log_stage(message: str):
    print(message)


# ---------------- Memory Load ---------------- #

def load_memory_node(state: GraphState):

    log_stage("Memory Loaded")

    session_id = state.get("session_id", "default")
    context = memory_manager.build_context_block(session_id, state["prompt"])
    memory_context = f"""Conversation History
{context['history_text']}

Project Memory
{context['project_text']}

Relevant Memory
{context['relevant_text']}"""

    return {
        "session_id": session_id,
        "prompt": state["prompt"],
        "memory_context": memory_context,
        "history_text": context["history_text"],
        "project_text": context["project_text"],
    }


# ---------------- Planner ---------------- #

def planner_node(state: GraphState):

    log_stage("Planner Started")

    planner_prompt = memory_manager.build_planner_prompt(state["prompt"], state.get("session_id", "default"))
    plan = planner.run(planner_prompt, state.get("memory_context", ""))

    log_stage("Planner Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": plan,
    }


# ---------------- Architect ---------------- #

def architect_node(state: GraphState):

    log_stage("Architect Started")

    architecture_input = f"""Planner Output
{state['plan']}"""
    architecture = architect.run(architecture_input, state.get("memory_context", ""))

    log_stage("Architect Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
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

    log_stage("Architecture Validator Started")

    architecture = enforce_architecture_sections(state["architecture"])

    log_stage("Architecture Validator Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": architecture,
    }


# ---------------- Router ---------------- #

def router_node(state: GraphState):

    log_stage("Router Started")

    route = router.route(state["prompt"], state.get("memory_context", ""))

    log_stage(f"Router Selected {route.title()}Agent")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": route,
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

Planner Output
{state.get('plan', '')}

Architect Output
{state.get('architecture', '')}

Previous Agent Output
{previous_output}

Current Task
{state['prompt']}"""


# ---------------- Agent Nodes ---------------- #

def coding_node(state: GraphState):

    log_stage("Coding Started")

    enhanced_prompt = build_agent_context(state, previous_output=state.get("architecture", ""))
    response = coding.run(enhanced_prompt, state.get("memory_context", ""), state.get("plan", ""))

    log_stage("Coding Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "coding",
        "generated_code": response,
        "response": response,
    }


def debug_node(state: GraphState):

    log_stage("Debug Started")

    enhanced_prompt = build_agent_context(state, previous_output=state.get("architecture", ""))
    response = debug.run(enhanced_prompt, state.get("memory_context", ""), state.get("plan", ""))

    log_stage("Debug Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "debug",
        "generated_code": response,
        "response": response,
    }


def resume_node(state: GraphState):

    log_stage("Resume Started")

    enhanced_prompt = build_agent_context(state, previous_output=state.get("architecture", ""))
    response = resume.run(enhanced_prompt, state.get("memory_context", ""), state.get("plan", ""))

    log_stage("Resume Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "resume",
        "generated_code": response,
        "response": response,
    }


def explanation_node(state: GraphState):

    log_stage("Explanation Started")

    previous_output = state.get("reviewed_code") or state.get("generated_code") or state.get("architecture", "")
    enhanced_prompt = build_agent_context(state, previous_output=previous_output)
    response = explanation.run(enhanced_prompt, state.get("memory_context", ""), previous_output)

    log_stage("Explanation Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "explanation",
        "explanation": response,
        "response": response,
    }


def reviewer_node(state: GraphState):

    log_stage("Reviewer Started")

    previous_output = state.get("generated_code", "")
    review_prompt = build_agent_context(state, previous_output=previous_output)
    response = reviewer.run(review_prompt, state.get("memory_context", ""), previous_output)

    log_stage("Reviewer Completed")

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "reviewer",
        "generated_code": state.get("generated_code", ""),
        "reviewed_code": response,
        "response": response,
    }


def save_memory_node(state: GraphState):

    log_stage("Save Memory Started")

    session_id = state.get("session_id", "default")
    agent_name = state.get("agent_name", state.get("route", "coding"))
    final_response = state.get("explanation") or state.get("reviewed_code") or state.get("response", "")

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

    return {
        "session_id": session_id,
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "coding"),
        "agent_name": agent_name,
        "generated_code": state.get("generated_code", ""),
        "reviewed_code": state.get("reviewed_code", ""),
        "explanation": state.get("explanation", ""),
        "response": final_response,
    }


def route_selector(state: GraphState):

    route = state.get("route", "coding")

    if route == "debug":
        return "debug"

    if route == "resume":
        return "resume"

    if route == "explanation":
        return "explanation"

    return "coding"


# ---------------- Graph ---------------- #

builder = StateGraph(GraphState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("architecture_validator", architecture_validator_node)
builder.add_node("router", router_node)
builder.add_node("coding", coding_node)
builder.add_node("debug", debug_node)
builder.add_node("resume", resume_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("explanation", explanation_node)
builder.add_node("save_memory", save_memory_node)

builder.set_entry_point("load_memory")

builder.add_edge("load_memory", "planner")
builder.add_edge("planner", "architect")
builder.add_edge("architect", "architecture_validator")
builder.add_edge("architecture_validator", "router")
builder.add_conditional_edges(
    "router",
    route_selector,
    {
        "coding": "coding",
        "debug": "debug",
        "resume": "resume",
        "explanation": "explanation",
    }
)
builder.add_edge("coding", "reviewer")
builder.add_edge("debug", "reviewer")
builder.add_edge("resume", "explanation")
builder.add_edge("reviewer", "explanation")
builder.add_edge("explanation", "save_memory")
builder.add_edge("save_memory", END)

graph = builder.compile()