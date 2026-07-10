from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.planner_agent import PlannerAgent


class AgentFactory:

    @staticmethod
    def create_agent(agent_type):

        if agent_type == "coding":
            return CodingAgent()

        elif agent_type == "debug":
            return DebugAgent()

        elif agent_type == "explanation":
            return ExplanationAgent()

        elif agent_type == "planner":
            return PlannerAgent()

        else:
            return CodingAgent()