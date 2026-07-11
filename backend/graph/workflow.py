from typing import TypedDict
from langgraph.graph import StateGraph, END

try:
    from ..agents.planner_agent import PlannerAgent
    from ..agents.router_agent import RouterAgent
except ImportError:
    from agents.planner_agent import PlannerAgent
    from agents.router_agent import RouterAgent


class GraphState(TypedDict):
    prompt: str
    plan: str
    response: str


planner = PlannerAgent()
router = RouterAgent()


def planner_node(state: GraphState):
    plan = planner.run(state["prompt"])

    return {
        "prompt": state["prompt"],
        "plan": plan,
    }


def router_node(state: GraphState):

    enhanced_prompt = f"""
Implementation Plan:

{state['plan']}

User Request:

{state['prompt']}
"""

    response = router.run(enhanced_prompt)

    return {
        "prompt": state["prompt"],
        "plan": state["plan"],
        "response": response,
    }


builder = StateGraph(GraphState)

builder.add_node("planner", planner_node)
builder.add_node("router", router_node)

builder.set_entry_point("planner")

builder.add_edge("planner", "router")
builder.add_edge("router", END)

graph = builder.compile()