from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent


class AgentFactory:

    @staticmethod
    def get_agent(agent_type):

        if agent_type == "coding":
            return CodingAgent()

        elif agent_type == "debug":
            return DebugAgent()

        elif agent_type == "resume":
            return ResumeAgent()

        elif agent_type == "explanation":
            return ExplanationAgent()

        else:
            raise ValueError("Invalid agent")