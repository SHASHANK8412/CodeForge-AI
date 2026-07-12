from typing import TypedDict
from langgraph.graph import StateGraph, END

from backend.agents.planner_agent import PlannerAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.router_agent import RouterAgent
from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent
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


# ---------------- Memory Load ---------------- #

def load_memory_node(state: GraphState):

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

    planner_prompt = memory_manager.build_planner_prompt(state["prompt"], state.get("session_id", "default"))
    plan = planner.run(planner_prompt, state.get("memory_context", ""))

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": plan,
    }


# ---------------- Architect ---------------- #

def architect_node(state: GraphState):

    architecture_input = f"""Planner Output
{state['plan']}"""
    architecture = architect.run(architecture_input, state.get("memory_context", ""))

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

    architecture = enforce_architecture_sections(state["architecture"])

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": architecture,
    }


# ---------------- Router ---------------- #

def router_node(state: GraphState):

    route = router.route(state["prompt"], state.get("memory_context", ""))

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


# ---------------- Agent Nodes ---------------- #

def coding_node(state: GraphState):
    enhanced_prompt = build_enhanced_prompt(state)
    response = coding.run(enhanced_prompt, state.get("memory_context", ""))

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "coding",
        "response": response,
    }


def debug_node(state: GraphState):

    enhanced_prompt = build_enhanced_prompt(state)
    response = debug.run(enhanced_prompt, state.get("memory_context", ""))

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "debug",
        "response": response,
    }


def resume_node(state: GraphState):

    enhanced_prompt = build_enhanced_prompt(state)
    response = resume.run(enhanced_prompt, state.get("memory_context", ""))

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "resume",
        "response": response,
    }


def explanation_node(state: GraphState):

    enhanced_prompt = build_enhanced_prompt(state)
    response = explanation.run(enhanced_prompt, state.get("memory_context", ""))

    return {
        "session_id": state.get("session_id", "default"),
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "agent_name": "explanation",
        "response": response,
    }


def save_memory_node(state: GraphState):

    session_id = state.get("session_id", "default")
    agent_name = state.get("agent_name", state.get("route", "coding"))

    memory_manager.save_interaction(
        session_id=session_id,
        user_prompt=state["prompt"],
        ai_response=state.get("response", ""),
        agent_name=agent_name,
        route=state.get("route", "coding"),
        plan=state.get("plan", ""),
        architecture=state.get("architecture", ""),
    )

    return {
        "session_id": session_id,
        "prompt": state["prompt"],
        "memory_context": state.get("memory_context", ""),
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "route": state.get("route", "coding"),
        "agent_name": agent_name,
        "response": state.get("response", ""),
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
builder.add_edge("coding", "save_memory")
builder.add_edge("debug", "save_memory")
builder.add_edge("resume", "save_memory")
builder.add_edge("explanation", "save_memory")
builder.add_edge("save_memory", END)

graph = builder.compile()