from backend.agents.factory import AgentFactory


class RouterAgent:

    def route(self, user_prompt: str, memory_context: str = ""):

        prompt = user_prompt.lower()
        memory_hint = memory_context.lower()

        # Continue previous conversation
        if any(
            phrase in prompt
            for phrase in [
                "continue",
                "proceed",
                "next",
                "resume where we left off",
            ]
        ):
            if "resume" in memory_hint:
                return "resume"

            if "debug" in memory_hint or "error" in memory_hint:
                return "debug"

            if "explain" in memory_hint or "architecture" in memory_hint:
                return "explanation"

            if "rag" in memory_hint or "document" in memory_hint:
                return "rag"

            if "frontend" in memory_hint or "react" in memory_hint:
                return "frontend"

            return "coding"

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

        rag_keywords = [
            "pdf",
            "document",
            "documents",
            "knowledge",
            "rag",
            "search document",
            "search pdf",
            "find in document",
            "skills",
            "programming languages",
            "technologies",
            "frameworks",
            "certifications",
            "projects",
            "experience",
            "education",
            "database",
        ]

        frontend_keywords = [
            "frontend",
            "react",
            "vite",
            "tailwind",
            "css",
            "html",
            "javascript",
            "jsx",
            "tsx",
            "navbar",
            "sidebar",
            "footer",
            "dashboard",
            "landing page",
            "login page",
            "signup page",
            "portfolio",
            "ui",
            "ux",
            "component",
            "page",
            "responsive",
            "hero section",
            "card",
            "form",
            "modal",
            "button",
        ]

        planner_keywords = [
            "plan",
            "roadmap",
            "project plan",
            "schedule",
            "steps",
            "workflow",
        ]

        architect_keywords = [
            "architecture",
            "system design",
            "design architecture",
            "microservices",
            "database design",
            "erd",
            "uml",
        ]

        reviewer_keywords = [
            "review",
            "code review",
            "optimize",
            "improve code",
            "best practices",
            "refactor",
        ]

        testing_keywords = [
            "test",
            "testing",
            "pytest",
            "unit test",
            "integration test",
            "test case",
            "coverage",
        ]

        # Routing Priority

        if any(word in prompt for word in debug_keywords):
            return "debug"

        if any(word in prompt for word in resume_keywords):
            return "resume"

        if any(word in prompt for word in rag_keywords):
            return "rag"

        if any(word in prompt for word in planner_keywords):
            return "planner"

        if any(word in prompt for word in architect_keywords):
            return "architect"

        if any(word in prompt for word in reviewer_keywords):
            return "reviewer"

        if any(word in prompt for word in testing_keywords):
            return "testing"

        if any(word in prompt for word in frontend_keywords):
            return "frontend"

        if any(word in prompt for word in explanation_keywords):
            return "explanation"

        return "coding"

    def run(self, user_prompt: str, memory_context: str = ""):

        agent_type = self.route(user_prompt, memory_context)

        print(f"[Router] Selected Agent: {agent_type}")

        agent = AgentFactory.create_agent(agent_type)

        return agent.run(user_prompt, memory_context)