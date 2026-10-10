from backend.agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert React Frontend Engineer.

Return COMPLETE production-ready JSX source code for every requested frontend file.

CRITICAL DIRECTIVES:
- Include the code files inside markdown blocks annotated with the filename in comments:
```jsx
// filename: frontend/src/App.jsx
import React from 'react';
...
```
- Every component file MUST contain full state management, JSX rendering, event handlers, and styling.
- Do NOT return placeholders, TODO comments, 'implement here' stubs, abbreviated implementations, or comments describing missing functionality.
- Do NOT write bullet points, instructions, or text descriptions. Return actual React source code files.
""",
            task_name="frontend",
        )

    def run(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(prompt, memory_context, previous_output)