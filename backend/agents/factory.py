from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.resume_agent import ResumeAgent


class AgentFactory:

    @staticmethod
    def get_agent(agent_name):

        if agent_name == "coding":
            return CodingAgent()

        elif agent_name == "debug":
            return DebugAgent()

        elif agent_name == "explanation":
            return ExplanationAgent()

        elif agent_name == "resume":
            return ResumeAgent()

        return CodingAgent()