# 🚀 AIForge v1.0 – Autonomous Multi-Agent AI Software Engineering Platform

[![Build Status](https://img.shields.io/badge/Build-Passing-emerald?style=for-the-badge&logo=github)](https://github.com/SHASHANK8412/CodeForge-AI)
[![Version](https://img.shields.io/badge/Version-v1.0.0--Release-indigo?style=for-the-badge)](https://github.com/SHASHANK8412/CodeForge-AI/releases)
[![License](https://img.shields.io/badge/License-MIT-amber?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)

> **AIForge** is an enterprise-grade, self-improving, autonomous multi-agent AI software engineering platform. It transforms natural language software requirements into production-grade, tested, documented, containerized, and deployable applications.

---

## 🌟 Key Highlights & v1.0 Capabilities

- 🤖 **12 Autonomous Specialized Agents**: Planner, Architect, Frontend, Backend, Database, API, Security, DevOps, Testing, Reviewer, Learning, and Refactor Agents.
- ⚡ **Parallel Multi-Agent Architecture**: Built with LangGraph, FastAPI, and React/Vite. Executes frontend, backend, database, and documentation generation concurrently.
- 🧠 **Continuous Learning & Semantic Project Memory**: SQLite long-term project memory database (`memory.db`), semantic vector similarity search, and automated lessons learned extraction.
- 🤝 **AI Pair Programmer Mode**: Targeted incremental code modifications, file locator, dependency graph builder (`dependency_graph.json`), safe backup system (`.backup/`), and unified diff patch generator.
- 🛠️ **Autonomous Refactoring & Debt Reduction**: AST code smell detection, Cyclomatic Complexity reduction (18 $\rightarrow$ 7), print statement to structured logger replacement, and security anti-pattern fixes.
- 📊 **AI Reflection & Quality Scoring**: 6-category weighted score evaluation (Architecture, Code Quality, Security, Performance, Testing, Documentation $\rightarrow$ **95.6% Overall AI Score**).
- 🏪 **Enterprise Plugin Marketplace**: Support for Planner Packs, UI Packs, Testing Packs, Architecture Packs, and Prompt Packs.
- 🚀 **One-Click CI/CD & Deployment**: GitHub commit & push, Docker image packaging, and cloud deployment readiness.

---

## 🏛️ System Architecture Workflow

```text
User Natural Language Request
             │
             ▼
      Planner Agent
             │
             ▼
     Architect Agent
             │
 ┌───────────┼───────────┬───────────┬───────────┐
 ▼           ▼           ▼           ▼           ▼
Frontend  Backend    Database     DevOps    Documentation
 │           │           │           │           │
 └───────────┴───────────┼───────────┴───────────┘
                         ▼
                   Testing Agent
                         │
                         ▼
                   Reviewer Agent
                         │
                         ▼
                  Refactor Agent
           (AST Code Smell & Complexity Fixes)
                         │
                         ▼
                Learning & Reflection Engine
          (Long-Term SQLite Memory & Quality Scoring)
                         │
                         ▼
         Docker Containerization & GitHub Export
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Core AI Agent Engine** | Python 3.11+, LangGraph, Ollama (Qwen), RAG Embeddings |
| **Backend API** | FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| **Frontend UI** | React 18, Vite, TailwindCSS, Lucide Icons |
| **Database & Caching** | SQLite, PostgreSQL, MongoDB, Redis |
| **DevOps & Cloud** | Docker, Docker Compose, GitHub Actions CI/CD |

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Git & Docker (Optional)

### 2. Clone & Setup
```bash
git clone https://github.com/SHASHANK8412/CodeForge-AI.git
cd CodeForge-AI
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🧪 Verification & Test Suite Execution

Run the complete 100-Day verification suite:
```bash
python tests/verify_day98_99_100_grand_finale.py
```

Expected Output:
```text
======================================================================
 DAY 98, 99 & 100 GRAND FINALE VERIFICATION SUMMARY: [PASS]
 Passed: 12 | Failed: 0
======================================================================
```

---

## 📄 License & Roadmap

- License: [MIT License](LICENSE)
- Roadmap: See [ROADMAP.md](ROADMAP.md) for v1.1 & v2.0 releases.
- Deployment Guide: See [DEPLOYMENT.md](DEPLOYMENT.md).
