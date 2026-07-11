# Day 11: Architect Agent Integration

## Overview
Day 11 introduces the Architect Agent as the bridge between planning and implementation.

The Planner Agent defines what should be built.
The Architect Agent defines how it should be built.

## Workflow Placement
Current LangGraph flow:

1. Planner
2. Architect
3. Architecture Validator
4. Router
5. Specialized execution agent (Coding, Debug, Resume, Explanation)

## Architect Agent Contract
Input:
- Planner output (project implementation plan)

Output:
- Structured architecture document in Markdown with implementation-ready sections.

Required architecture sections:
- Project Architecture
- Folder Structure
- Frontend Files
- Backend Files
- Database Schema
- API Routes
- Dependencies

## Architecture Validator
The Architecture Validator runs immediately after the Architect node.

It checks for required sections and appends a quality warning if any are missing.
This ensures downstream agents receive architecture guidance that is complete enough for execution.

## Router Behavior
The Router decides which specialized agent handles the final step:
- coding
- debug
- resume
- explanation

The graph now uses conditional edges, so Router output determines the next node.

## Testing
Day 11 adds pytest tests for:
- Route selection paths (coding, debug, resume, explanation)
- Architecture validation behavior
- End-to-end graph routing with mocked agents

## Run Commands
From project root:

FastAPI:
python -m uvicorn backend.main:app --reload --app-dir .

Graph test:
python -m backend.graph.test_graph

Pytest:
pytest tests/test_day11_workflow.py -q
