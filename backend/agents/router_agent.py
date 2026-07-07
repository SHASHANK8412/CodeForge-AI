from backend.agents.factory import AgentFactory


class RouterAgent:

    def get_agent(self, user_prompt):

        prompt = user_prompt.lower()

        if "bug" in prompt or "error" in prompt or "fix" in prompt:
            print("➡️ DebugAgent")
            return AgentFactory.get_agent("debug")

        elif "resume" in prompt or "linkedin" in prompt:
            print("➡️ ResumeAgent")
            return AgentFactory.get_agent("resume")

        elif "explain" in prompt or "what is" in prompt or "how" in prompt:
            print("➡️ ExplanationAgent")
            return AgentFactory.get_agent("explanation")

        else:
            print("➡️ CodingAgent")
            return AgentFactory.get_agent("coding")