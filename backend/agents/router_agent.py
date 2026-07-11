from backend.agents.factory import AgentFactory


class RouterAgent:

    def route(self, user_prompt):

        prompt = user_prompt.lower()

        if any(word in prompt for word in [
            "bug",
            "error",
            "fix",
            "issue",
            "exception"
        ]):
            return "debug"

        elif any(word in prompt for word in [
            "resume",
            "linkedin",
            "cv"
        ]):
            return "resume"

        elif any(word in prompt for word in [
            "explain",
            "what is",
            "how",
            "why"
        ]):
            return "explanation"

        return "coding"

    def run(self, user_prompt):

        agent_type = self.route(user_prompt)

        agent = AgentFactory.create_agent(agent_type)

        return agent.run(user_prompt)