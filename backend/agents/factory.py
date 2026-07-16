from backend.agents.coding_agent import CodingAgent
from backend.agents.debug_agent import DebugAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.planner_agent import PlannerAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.rag_agent import RAGAgent
from backend.agents.testing_agent import TestingAgent
from backend.agents.frontend_agent import FrontendAgent


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

        elif agent_type == "reviewer":
            return ReviewerAgent()

        elif agent_type == "rag":
            return RAGAgent()

        elif agent_type == "testing":
            return TestingAgent()

        elif agent_type == "frontend":
            return FrontendAgent()

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")