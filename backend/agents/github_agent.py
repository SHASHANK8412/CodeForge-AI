from backend.agents.base_agent import BaseAgent


class GitHubAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert DevOps and GitHub Engineer.

Your responsibilities are:

- Generate a clean project folder structure.
- Suggest file organization.
- Create a deployment checklist.
- Generate a Git commit message.
- Generate a GitHub repository description.
- Generate a README summary.

Return everything in Markdown format.
""",
            task_name="github",
        )

    def run(self, state):

        project = state.get("user_prompt", "")
        frontend = state.get("frontend", "")
        backend = state.get("backend", "")
        database = state.get("database", "")
        documentation = state.get("documentation", "")

        github_output = self.generate(
            f"""
Project:

{project}

Frontend:

{frontend}

Backend:

{backend}

Database:

{database}

Documentation:

{documentation}

Generate:

1. Recommended project folder structure
2. GitHub repository description
3. Git commit message
4. Deployment checklist
5. Final release checklist
"""
        )

        state["github"] = github_output

        return state

    async def run_async(self, state):

        project = state.get("user_prompt", "")
        frontend = state.get("frontend", "")
        backend = state.get("backend", "")
        database = state.get("database", "")
        documentation = state.get("documentation", "")

        github_output = await self.generate_async(
            f"""
Project:

{project}

Frontend:

{frontend}

Backend:

{backend}

Database:

{database}

Documentation:

{documentation}

Generate:

1. Recommended project folder structure
2. GitHub repository description
3. Git commit message
4. Deployment checklist
5. Final release checklist
"""
        )

        state["github"] = github_output

        return state