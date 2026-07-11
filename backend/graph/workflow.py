from typing import TypedDict
from langgraph.graph import StateGraph, END

from backend.agents.planner_agent import PlannerAgent
from backend.agents.router_agent import RouterAgent
from backend.agents.coding_agent import CodingAgent


class GraphState(TypedDict):
    prompt: str
    plan: str
    route: str
    response: str


planner = PlannerAgent()
router = RouterAgent()
coding = CodingAgent()


def planner_node(state: GraphState):

    plan = planner.run(state["prompt"])

    return {
        "prompt": state["prompt"],
        "plan": plan,
    }


def router_node(state: GraphState):

    route = router.route(state["prompt"])

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "route": route,
    }


def coding_node(state: GraphState):

    enhanced_prompt = f"""
Implementation Plan:

{state['plan']}

User Request:

{state['prompt']}
"""

    response = coding.run(enhanced_prompt)

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "route": state["route"],
        "response": response,
    }


builder = StateGraph(GraphState)

builder.add_node("planner", planner_node)
builder.add_node("router", router_node)
builder.add_node("coding", coding_node)

builder.set_entry_point("planner")

builder.add_edge("planner", "router")
builder.add_edge("router", "coding")
builder.add_edge("coding", END)

graph = builder.compile()