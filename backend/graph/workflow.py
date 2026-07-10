from typing import TypedDict
from langgraph.graph import StateGraph, END

try:
    from ..agents.factory import AgentFactory
except ImportError:
    from agents.factory import AgentFactory


class GraphState(TypedDict):
    prompt: str
    response: str


planner = AgentFactory.create_agent("coding")


def planner_node(state: GraphState):
    reply = planner.run(state["prompt"])

    return {
        "prompt": state["prompt"],
        "response": reply,
    }


builder = StateGraph(GraphState)

builder.add_node("planner", planner_node)

builder.set_entry_point("planner")

builder.add_edge("planner", END)

graph = builder.compile()