from backend.agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert React Frontend Engineer.

Generate the functional React frontend code.
Include the code files inside markdown blocks annotated with the filename in comments:
```jsx
// filename: frontend/src/App.jsx
import React from 'react';
...
```
Do NOT write text descriptions, bullet points, or instructions. Generate actual React source code files.
""",
            task_name="frontend",
        )

    def run(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(prompt, memory_context, previous_output)