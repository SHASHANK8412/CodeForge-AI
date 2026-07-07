from backend.agents.factory import AgentFactory


class RouterAgent:

    def route(self, user_prompt):

        prompt = user_prompt.lower()

        if "bug" in prompt or "error" in prompt or "fix" in prompt:
            agent = AgentFactory.get_agent("debug")

        elif "resume" in prompt or "linkedin" in prompt:
            agent = AgentFactory.get_agent("resume")

        elif "explain" in prompt or "what is" in prompt or "how" in prompt:
            agent = AgentFactory.get_agent("explanation")

        else:
            agent = AgentFactory.get_agent("coding")

        return agent.run(user_prompt)