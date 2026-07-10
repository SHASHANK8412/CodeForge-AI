try:
    from .coding_agent import CodingAgent
    from .debug_agent import DebugAgent
    from .resume_agent import ResumeAgent
    from .explanation_agent import ExplanationAgent
    from .planner_agent import PlannerAgent
except ImportError:
    from agents.coding_agent import CodingAgent
    from agents.debug_agent import DebugAgent
    from agents.resume_agent import ResumeAgent
    from agents.explanation_agent import ExplanationAgent
    from agents.planner_agent import PlannerAgent


class AgentFactory:

    @staticmethod
    def create_agent(agent_type: str):

        if agent_type == "coding":
            return CodingAgent()

        elif agent_type == "debug":
            return DebugAgent()

        elif agent_type == "resume":
            return ResumeAgent()

        elif agent_type == "explanation":
            return ExplanationAgent()

        elif agent_type == "planner":
            return PlannerAgent()

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")