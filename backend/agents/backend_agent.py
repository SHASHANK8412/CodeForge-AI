from backend.agents.base_agent import BaseAgent


class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert FastAPI backend engineer.

Generate ONLY:

# API Endpoints

# Folder Structure

# Models

Rules:
- Be concise. Short bullet points, not full implementations.
- No full source code, no long explanations.
- Maximum 500 words.
""",
            task_name="backend",
        )

    def run(self, state):

        architecture = state.get("architecture", "")
        plan = state.get("plan", "")
        prompt = state.get("user_prompt", "")

        backend_code = self.generate(
            f"""
Project:

{prompt}

Plan:

{plan}

Architecture:

{architecture}

Generate ONLY the API Endpoints, Folder Structure, and Models. Do NOT generate full implementations.
"""
        )

        state["backend"] = backend_code

        return state

    async def run_async(self, state):

        architecture = state.get("architecture", "")
        plan = state.get("plan", "")
        prompt = state.get("user_prompt", "")

        backend_code = await self.generate_async(
            f"""
Project:

{prompt}

Plan:

{plan}

Architecture:

{architecture}

Generate ONLY the API Endpoints, Folder Structure, and Models. Do NOT generate full implementations.
"""
        )

        state["backend"] = backend_code

        return state