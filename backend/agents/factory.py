from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent


class AgentFactory:

    @staticmethod
    def get_agent(agent_name):

        if agent_name == "coding":
            return CodingAgent()

        if agent_name == "debug":
            return DebugAgent()

        return CodingAgent()