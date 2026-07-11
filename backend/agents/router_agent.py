try:
    from .factory import AgentFactory
except ImportError:
    from agents.factory import AgentFactory


class RouterAgent:

    def route(self, user_prompt):

        prompt = user_prompt.lower()

        # Debug Agent
        if any(word in prompt for word in [
            "bug",
            "error",
            "fix",
            "issue",
            "exception"
        ]):
            agent = AgentFactory.create_agent("debug")

        # Resume Agent
        elif any(word in prompt for word in [
            "resume",
            "linkedin",
            "cv"
        ]):
            agent = AgentFactory.create_agent("resume")

        # Explanation Agent
        elif any(word in prompt for word in [
            "explain",
            "what is",
            "how",
            "why"
        ]):
            agent = AgentFactory.create_agent("explanation")

        # Everything else goes to Coding Agent
        else:
            agent = AgentFactory.create_agent("coding")

        return agent.run(user_prompt)

    def run(self, user_prompt):
        return self.route(user_prompt)