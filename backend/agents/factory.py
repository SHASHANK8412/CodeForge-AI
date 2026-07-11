from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.planner_agent import PlannerAgent
from backend.agents.architect_agent import ArchitectAgent


class AgentFactory:

    @staticmethod
    def create_agent(agent_type: str):

        if agent_type == "coding":
            return CodingAgent()

        elif agent_type == "debug":
            return DebugAgent()

        elif agent_type == "resume":
            return ResumeAgent()
        
        elif agent_type == "architect":
            return ArchitectAgent()

        elif agent_type == "explanation":
            return ExplanationAgent()

        elif agent_type == "planner":
            return PlannerAgent()

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")