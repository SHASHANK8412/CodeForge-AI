# Day 12: AIForge Memory System

## What Changed
Day 12 adds a persistent, session-scoped memory layer so AIForge can remember previous prompts, project context, and agent decisions.

## Memory Layers

### Conversation Memory
Stores:
- User prompt
- AI response
- Timestamp
- Session ID
- Agent name
- Route

### Project Memory
Stores:
- Current project
- Frontend stack
- Backend stack
- Database
- Completed tasks
- Pending tasks
- Generated files
- Latest plan
- Latest architecture
- Last agent
- Last task

### Vector Memory
Stores searchable text snippets for lightweight semantic recall across a session.

## Workflow Placement
Current graph:
1. Load Memory
2. Planner
3. Architect
4. Architecture Validator
5. Router
6. Routed Agent
7. Save Memory

## API Endpoints
- GET /memory/history
- GET /memory/project
- DELETE /memory/clear

## Session Handling
Each session uses its own memory files, so conversations do not mix across users or projects.

## Prompt Flow
The Planner receives:
- Current prompt
- Previous messages
- Project status

The Router receives:
- Previous prompts
- Last task
- Current project
- Previously used agent

The Coding Agent receives:
- Project context
- Conversation history
- Relevant memory
- Current task
- Planner output
- Architect output

## Testing
Day 12 tests cover:
- Conversation persistence
- Project memory updates
- Session isolation
- Memory carryover between prompts
- Graph execution with mocked agents

## Run Commands
From project root:

Run API:
python -m uvicorn backend.main:app --reload --app-dir .

Run workflow test:
python -m backend.graph.test_graph

Run tests:
pytest tests/test_day12_memory.py -q
