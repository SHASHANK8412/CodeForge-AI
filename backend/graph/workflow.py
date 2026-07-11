from typing import TypedDict
from langgraph.graph import StateGraph, END

from backend.agents.planner_agent import PlannerAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.router_agent import RouterAgent
from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent


class GraphState(TypedDict):
    prompt: str
    plan: str
    architecture: str
    route: str
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


# ---------------- Planner ---------------- #

def planner_node(state: GraphState):

    plan = planner.run(state["prompt"])

    return {
        "prompt": state["prompt"],
        "plan": plan,
    }


# ---------------- Architect ---------------- #

def architect_node(state: GraphState):

    architecture = architect.run(state["plan"])

    return {
        "prompt": state["prompt"],
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
        "prompt": state["prompt"],
        "plan": state["plan"],
        "architecture": architecture,
    }


# ---------------- Router ---------------- #

def router_node(state: GraphState):

    route = router.route(state["prompt"])

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": route,
    }


# ---------------- Shared Context ---------------- #

def build_enhanced_prompt(state: GraphState) -> str:

    return f"""
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
    response = coding.run(enhanced_prompt)

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "response": response,
    }


def debug_node(state: GraphState):

    enhanced_prompt = build_enhanced_prompt(state)
    response = debug.run(enhanced_prompt)

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "response": response,
    }


def resume_node(state: GraphState):

    enhanced_prompt = build_enhanced_prompt(state)
    response = resume.run(enhanced_prompt)

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "response": response,
    }


def explanation_node(state: GraphState):

    enhanced_prompt = build_enhanced_prompt(state)
    response = explanation.run(enhanced_prompt)

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "architecture": state["architecture"],
        "route": state["route"],
        "response": response,
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

builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("architecture_validator", architecture_validator_node)
builder.add_node("router", router_node)
builder.add_node("coding", coding_node)
builder.add_node("debug", debug_node)
builder.add_node("resume", resume_node)
builder.add_node("explanation", explanation_node)

builder.set_entry_point("planner")

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
builder.add_edge("coding", END)
builder.add_edge("debug", END)
builder.add_edge("resume", END)
builder.add_edge("explanation", END)

graph = builder.compile()