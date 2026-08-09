import json
import re
import logging
from typing import Dict, Any, Tuple
from backend.agents.base_agent import BaseAgent
from backend.schemas.agent_contract import ProjectSpec

_logger = logging.getLogger("aiforge.planner_agent")


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are the Chief Software Architect of AIForge — a Senior Technical Lead with 20+ years of
experience shipping production software. Before any code is written, you analyze the user's
project idea and produce a professional requirements and discovery report.

You never ask clarifying questions. Where the request is ambiguous, state an explicit,
reasonable assumption instead, so downstream AI agents (Architect, Backend, Frontend, Database,
Testing, Deployment) can proceed autonomously with zero back-and-forth.

Produce EXACTLY these 9 sections, in this order, using Markdown `##` headings:

## 1. Executive Summary
2-4 sentences: what the product is, who it is for, and its core value proposition.

## 2. Functional Requirements
Numbered list of concrete capabilities the system must have (FR-1, FR-2, FR-3, ...).

## 3. Non-Functional Requirements
Bullet list covering performance, scalability, security, availability, and usability targets.

## 4. User Stories
3-8 stories, each written as: "As a <role>, I want <capability>, so that <benefit>."

## 5. Acceptance Criteria
For each major user story, 2-3 bullet criteria (Given/When/Then or a plain checklist).

## 6. Assumptions
Bullet list of assumptions made to avoid needing clarification (target scale, auth model,
budget tier, single-tenant vs multi-tenant, etc.).

## 7. Constraints
Bullet list of technical, business, or timeline constraints implied or stated by the request.

## 8. Domain Detection
One line naming the product domain/category (e.g. E-Commerce, Social Media, Streaming/Media,
SaaS/B2B Dashboard, FinTech, Healthcare, Developer Tools, Marketplace) plus a one-sentence
justification.

## 9. Recommended Tech Stack
Bullet list: Frontend, Backend, Database, Auth, Infra/Hosting, and any domain-specific services
(payment gateway, video CDN, real-time transport, etc.). Justify each pick in one line.

Rules:
- Be specific and concrete to the actual product implied by the prompt — never generic filler.
- No code. Use bullets and short lines, not paragraphs. Keep each section under ~80 words.
- End the response with one fenced ```json code block — nothing after it — containing a
  machine-readable summary that downstream agents can parse directly without re-reading the
  Markdown, in exactly this shape (omit a field only if genuinely not applicable):

```json
{
  "project_name": "",
  "domain": "",
  "executive_summary": "",
  "functional_requirements": ["FR-1: ..."],
  "non_functional_requirements": [""],
  "user_stories": ["As a ... I want ... so that ..."],
  "assumptions": [""],
  "constraints": [""],
  "tech_stack": {"frontend": "", "backend": "", "database": "", "auth": "", "infra": ""}
}
```

- The JSON must be syntactically valid and must match the Markdown content above.
            """,
            task_name="planner",
        )

    def run(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(prompt, memory_context, previous_output)

    def parse_plan_json(self, raw_output: str, allow_fallback: bool = False) -> Dict[str, Any]:
        """
        Parses LLM output into a validated ProjectSpec dictionary.
        Extracts JSON code block, parses with json.loads, and validates via Pydantic ProjectSpec.
        Raises ValueError on malformed/invalid JSON unless allow_fallback=True.
        """
        if not raw_output or not isinstance(raw_output, str):
            if not allow_fallback:
                raise ValueError("Empty or non-string output received from PlannerAgent.")
            _logger.warning("Empty or non-string output passed to parse_plan_json. Returning default spec.")
            return ProjectSpec().model_dump()

        extracted_json_str = ""
        # 1. Regex search used ONLY to locate fenced JSON block ```json ... ```
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_output, re.IGNORECASE)
        if json_match:
            extracted_json_str = json_match.group(1).strip()
        else:
            # 2. Substring search fallback for first { and last }
            first_brace = raw_output.find("{")
            last_brace = raw_output.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extracted_json_str = raw_output[first_brace:last_brace + 1].strip()

        if not extracted_json_str:
            if not allow_fallback:
                raise ValueError("Planner output did not contain a valid JSON block.")
            _logger.warning("No JSON block found in planner output. Returning fallback spec.")

        parsed_data = {}
        if extracted_json_str:
            try:
                parsed_data = json.loads(extracted_json_str, strict=False)
            except Exception as e:
                if not allow_fallback:
                    raise ValueError(f"Planner output JSON parsing failed: {e}")
                _logger.warning(f"Failed to parse JSON from planner output: {e}. Attempting fallback.")

        # 3. Coerce tech_stack picks if provided as dict
        tech_stack = parsed_data.get("tech_stack", {}) if isinstance(parsed_data.get("tech_stack"), dict) else {}
        frontend_pick = tech_stack.get("frontend") or parsed_data.get("frontend", "React")
        backend_pick = tech_stack.get("backend") or parsed_data.get("backend", "FastAPI")
        database_pick = tech_stack.get("database") or parsed_data.get("database", "PostgreSQL")

        func_reqs = parsed_data.get("functional_requirements", [])
        if not isinstance(func_reqs, list):
            func_reqs = [str(func_reqs)]

        all_reqs = parsed_data.get("requirements", func_reqs)
        if not isinstance(all_reqs, list):
            all_reqs = [str(all_reqs)]

        # 4. Construct Pydantic ProjectSpec model with schema validation
        spec_kwargs = {
            "project_name": parsed_data.get("project_name") or "AIForge Application",
            "domain": parsed_data.get("domain") or "Web Application",
            "type": parsed_data.get("type") or "Full Stack Web App",
            "executive_summary": parsed_data.get("executive_summary") or "",
            "requirements": all_reqs,
            "functional_requirements": func_reqs,
            "non_functional_requirements": parsed_data.get("non_functional_requirements", []),
            "user_stories": parsed_data.get("user_stories", []),
            "assumptions": parsed_data.get("assumptions", []),
            "constraints": parsed_data.get("constraints", []),
            "pages": parsed_data.get("pages") or ["Home", "Dashboard"],
            "features": parsed_data.get("features") or func_reqs or ["Authentication", "CRUD API"],
            "frontend": str(frontend_pick),
            "backend": str(backend_pick),
            "database": str(database_pick),
            "dependencies": parsed_data.get("dependencies", []),
            "api_requirements": parsed_data.get("api_requirements", []),
            "important_constraints": parsed_data.get("important_constraints") or parsed_data.get("constraints", []),
            "tech_stack": tech_stack
        }

        validated_spec = ProjectSpec(**spec_kwargs)
        plan_dict = validated_spec.model_dump()

        return plan_dict


    def generate_structured_spec(self, raw_output: str) -> Tuple[Dict[str, Any], ProjectSpec]:
        """
        Returns both legacy plan dictionary and validated Pydantic ProjectSpec model.
        """
        plan_dict = self.parse_plan_json(raw_output)
        spec_model = ProjectSpec(**plan_dict)
        return plan_dict, spec_model

