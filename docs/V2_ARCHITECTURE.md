# AIForge V2 Architecture Document
## "The Autonomous AI Software Engineering Company"

---

## 🏛️ Executive Vision

AIForge V2 evolves AIForge from a multi-agent prompt runner into an **Autonomous AI Software Engineering Company**.

The platform is structured into **15 specialized autonomous agent roles** collaborating across 7 operational layers.

---

## 🏢 Agent Hierarchy & Layer Structure

```text
User Client Request
        │
        ▼
   API Gateway (`/api/v2/...`)
        │
        ▼
   CEO Agent (Executive Scope & Complexity Evaluation)
        │
        ▼
   Project Manager Agent (Task Decomposition & Dependency Mapping)
        │
   ┌────┴──────────────────────────┬──────────────────────────┐
   ▼                               ▼                          ▼
Planner Agent               Architect Agent             DevOps Agent
   │                               │                          │
   └───────────────────────────────┼──────────────────────────┘
                                   ▼
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
      Frontend Agent        Backend Agent         Database Agent
    (React / Vite UI)     (FastAPI Backend)      (SQL Database)
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   ▼
                       Quality & Security Layer
                     (QA, Reviewer, Security Scan)
                                   ▼
                      Delivery & Monitoring Layer
                  (Docs, Deployment, Live Monitoring)
                                   ▼
                      Continuous Self-Learning Engine
```

---

## 📦 Modular Folder Structure

```text
AIForge-V2/
├── backend/                  # FastAPI Application Core & Existing Pipeline
├── frontend/                 # React + Vite UI Dashboard & Workspaces
├── v2/
│   ├── agents/               # 15 Specialized Autonomous Agent Roles
│   │   ├── ceo/              # Executive Request Evaluation & Resource Allocation
│   │   ├── manager/          # Work Decomposition & Sprint Planning
│   │   ├── planner/          # Requirements & Discovery Reports
│   │   ├── architect/        # System Topology & REST API Design
│   │   ├── frontend/         # React Component Engineering
│   │   ├── backend/          # FastAPI Backend Engineering
│   │   ├── database/         # SQL Schema & Migration Generation
│   │   ├── devops/           # Docker & CI/CD Pipelines
│   │   ├── qa/               # Automated Integration & Unit Testing
│   │   ├── reviewer/         # Static Code Quality Audit
│   │   ├── security/         # Security Scan & Vulnerability Reduction
│   │   ├── documentation/    # Technical Documentation
│   │   ├── deployment/       # Multi-Platform Deployments
│   │   ├── monitoring/       # Telemetry & SRE Health Audits
│   │   └── learning/         # Continuous Reflection & Lesson Capture
│   ├── configs/              # Centralized Configuration (LLM, DB, Redis, ChromaDB)
│   ├── logs/                 # Structured Agent Action Audit Engine
│   ├── events/               # Asynchronous Event Bus (PubSub)
│   ├── database/             # PostgreSQL Schema & ORM Models
│   ├── memory/               # Short-Term, Working & Project Memory
│   ├── vector_store/         # ChromaDB Vector Memory
│   ├── api/                  # V2 REST Gateway Routes
│   ├── projects/             # Generated Workspace Outputs
│   └── tests/                # V2 Test Suites
├── docs/                     # Documentation & Architecture Guides
└── tests/                    # System Verification Suites
```

---

## ⚡ Inter-Agent Communication Protocol

Agents communicate via structured Pydantic event messages:
- **`AgentMessage`**: `message_id`, `sender`, `recipient`, `task_type`, `payload`, `timestamp`
- **`TaskAssignment`**: `task_id`, `project_id`, `assigned_agent`, `title`, `description`, `dependencies`, `status`
- **`ProjectSpecification`**: `project_id`, `name`, `client_prompt`, `complexity_score`, `allocated_agents`, `estimated_timeline_hours`

---

## 🗄️ Database Tables Schema (PostgreSQL)

1. `Projects`: Project metadata, complexity, status
2. `Tasks`: Individual agent task assignments & execution state
3. `Agents`: Registered agent capabilities & execution metrics
4. `Messages`: Inter-agent event message log
5. `Logs`: Structured audit trail (inputs, outputs, tokens, execution time)
6. `Events`: Decoupled PubSub topic events
7. `Deployments`: Deployment artifacts & status
8. `Knowledge`: Lessons learned & reusable patterns
9. `Embeddings`: Vector embedding metadata
10. `Users`: User authentication & RBAC
11. `Sessions`: User session tokens
12. `Metrics`: Real-time system performance telemetry
