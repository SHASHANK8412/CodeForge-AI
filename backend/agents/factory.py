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
        agent_type_upper = (agent_type or "").upper()
        agent_type_lower = (agent_type or "").lower()

        if agent_type_upper in ["CODING", "CODE_GENERATION", "DSA_PROBLEM"] or agent_type_lower == "coding":
            return CodingAgent()

        elif agent_type_upper == "DEBUGGING" or agent_type_lower == "debug":
            return DebugAgent()

        elif agent_type_upper == "RESUME" or agent_type_lower == "resume":
            return ResumeAgent()

        elif agent_type_upper == "EXPLANATION" or agent_type_upper == "GENERAL_QA" or agent_type_lower == "explanation":
            return ExplanationAgent()

        elif agent_type_upper == "RAG_QUERY" or agent_type_lower == "rag":
            return RAGAgent()

        elif agent_type_upper == "PROJECT_GENERATION" or agent_type_lower == "project_manager":
            from backend.agents.project_manager_agent import ProjectManagerAgent
            return ProjectManagerAgent()

        elif agent_type_lower == "architect":
            return ArchitectAgent()

        elif agent_type_lower == "planner":
            return PlannerAgent()

        elif agent_type_lower == "reviewer":
            return ReviewerAgent()

        elif agent_type_lower == "testing":
            return TestingAgent()

        elif agent_type_lower == "frontend":
            return FrontendAgent()

        elif agent_type_upper == "UNKNOWN":
            # UNKNOWN defaults to ExplanationAgent as a safe general fallback (NEVER CodingAgent!)
            return ExplanationAgent()

        else:
            raise ValueError(f"Unknown agent type or intent: {agent_type}")