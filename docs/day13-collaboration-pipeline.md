# Day 13: Multi-Agent Collaboration Pipeline

## Goal
Transform AIForge from isolated single-purpose agents into a collaborative pipeline where agents build on each other’s work.

## New Workflow
1. Conversation Memory loads session context.
2. Planner creates the plan.
3. Memory Manager enriches the context.
4. Router selects the primary route.
5. Coding or Debug generates the first solution.
6. Reviewer improves the generated output.
7. Explanation Agent explains the final result.
8. Memory saves the interaction.

## Agent-to-Agent Communication
Agents now receive:
- User prompt
- Conversation memory
- Project memory
- Previous agent output

## Reviewer Agent
The Reviewer Agent:
- Reviews generated code
- Detects bugs
- Improves readability
- Improves naming
- Suggests optimizations
- Applies best practices

## Routing Behavior
- `coding` and `debug` routes flow into `reviewer`
- `resume` routes flow directly into `explanation`
- `explanation` routes can return explanatory output directly

## Logging
The workflow logs major lifecycle stages:
- Planner Started / Completed
- Memory Loaded
- Router Selected ...
- Coding Started / Completed
- Reviewer Started / Completed
- Explanation Started / Completed
- Workflow Finished

## Testing
Covered with mocked execution paths for:
- Create Login API -> coding -> reviewer -> explanation
- Explain previous code -> explanation
- Fix previous bug -> debug -> reviewer -> explanation
- Generate Resume -> resume -> explanation

## Run Commands
From project root:

Run API:
python -m uvicorn backend.main:app --reload --app-dir .

Run workflow test:
python -m backend.graph.test_graph

Run pytest:
pytest tests/test_day13_collaboration.py -q
