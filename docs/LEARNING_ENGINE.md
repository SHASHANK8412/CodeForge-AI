# AIForge V2 – Production-Ready Learning Engine (Day 41 Documentation)

## Architecture Overview

The **Production-Ready Learning Engine** elevates AIForge V2 into an autonomous system that continuously learns and improves from previous project generations, bug fixes, architecture decisions, and agent execution metrics.

```text
User Request / Prompt
          │
          ▼
       Planner
          │
          ▼
   Learning Enricher  ◄─── Reads previous project blueprints, bug memory & patterns
          │
          ▼
    Project Manager
          │
          ▼
   Architect Engine
          │
          ▼
    Development (Frontend, Backend, DB)
          │
          ▼
Reviewer & Testing (Fixes bugs & records solutions)
          │
          ▼
    Documentation
          │
          ▼
   Learning Updater   ───► Writes project profile, bug fixes & pattern templates
          │
          ▼
       Export
```

---

## Folder Structure

```text
backend/
    learning/
        project_memory.py       # Persistent project execution records & user feedback
        knowledge_store.py      # Bug memory (causes, solutions, confidence) & best practice library
        pattern_detector.py     # Reusable architecture & code pattern templates
        embedding_search.py     # Vector semantic search over past successful projects
        success_tracker.py      # Platform metrics, build times, agent performance tracking
        learning_engine.py      # Master Learning Engine (enrichment & knowledge updates)
        __init__.py

frontend/
    src/
        components/
            LearningDashboard.jsx  # React UI dashboard displaying learning analytics
```

---

## Key Learning Subsystems

### 1. Project Memory
Stores user prompts, architecture blueprints, generated file paths, tech stacks, execution times, test results, error logs, and user feedback ratings.

### 2. Bug Memory & Knowledge Ranking
Whenever the Reviewer or Testing Agent resolves an issue, the bug description, root cause, solution patch, and confidence score are saved. On future occurrences, the solution is automatically retrieved. Solutions are ranked using:
$$\text{Quality Score} = \text{Confidence Score} \times 100$$
$$\text{Success Rate \%} = \frac{\text{Usage Count}}{\text{Usage Count} + \text{Failure Count}} \times 100$$

### 3. Pattern Detection
Detects reusable patterns (`Dashboard`, `Authentication`, `REST API`, `Admin Panel`, `CRUD`, `React Components`, `FastAPI APIs`, `Database Schemas`) and converts them into reusable templates.

### 4. Semantic Search
Converts project prompts into vector representations to find matching historical blueprints without blind code duplication.

---

## REST API Endpoints

- `GET /learning/projects`: Retrieves all historical project records.
- `GET /learning/patterns`: Retrieves all detected reusable software patterns.
- `GET /learning/bugs`: Retrieves Bug Memory repository.
- `GET /learning/statistics`: Retrieves platform-wide learning analytics.
- `POST /learning/project`: Stores a generated project into persistent Project Memory.
- `POST /learning/feedback`: Submits user feedback rating and comments.
- `GET /learning/search`: Performs semantic vector search over past project blueprints.
- `GET /learning/dashboard`: Retrieves Learning Dashboard data.
