from backend.agents.factory import AgentFactory


class RouterAgent:

    def route(self, user_prompt: str):

        prompt = user_prompt.lower()

        debug_keywords = [
            "bug",
            "error",
            "fix",
            "issue",
            "exception",
            "traceback",
            "crash",
            "not working",
        ]

        resume_keywords = [
            "resume",
            "cv",
            "linkedin",
            "cover letter",
        ]

        explanation_keywords = [
            "explain",
            "what is",
            "how",
            "why",
            "difference",
            "compare",
            "teach",
        ]

        if any(word in prompt for word in debug_keywords):
            return "debug"

        if any(word in prompt for word in resume_keywords):
            return "resume"

        if any(word in prompt for word in explanation_keywords):
            return "explanation"

        return "coding"

    def run(self, user_prompt: str):

        agent_type = self.route(user_prompt)

        print(f"[Router] Selected Agent: {agent_type}")

        agent = AgentFactory.create_agent(agent_type)

        return agent.run(user_prompt)