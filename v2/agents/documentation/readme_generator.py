"""
AIForge V2 – README.md Generator
================================
Generates production-grade README.md files (Overview, Features, Stack, Installation, Usage, Project Tree).
"""

class ReadmeGenerator:

    def generate_readme(self, project_name: str) -> str:
        return f"""# {project_name}

> Production-ready software application generated autonomously by **AIForge V2**.

## 🚀 Features
- **Frontend**: React + TypeScript + Tailwind CSS UI components with Zustand state management.
- **Backend**: FastAPI REST framework with Pydantic validation schemas & JWT Bearer Auth.
- **Database**: PostgreSQL persistence layer with SQLAlchemy ORM models & Alembic migrations.
- **Testing**: Automated Pytest unit/integration suites, HTTPX API tests, and Playwright E2E specs.
- **Documentation**: Auto-generated developer guides, API references, and Mermaid architecture diagrams.

## 🛠️ Technology Stack
- **Languages**: Python 3.13, TypeScript, SQL
- **Frameworks**: FastAPI, React 18, React Router 6, Tailwind CSS
- **Database**: PostgreSQL 16, SQLAlchemy, Alembic, Redis
- **Testing**: Pytest, Vitest, Playwright, Locust

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### Local Development Setup
```bash
# 1. Clone Repository & Setup Environment
git clone https://github.com/SHASHANK8412/CodeForge-AI.git
cd CodeForge-AI

# 2. Start Backend API Server
python -m venv venv
source venv/bin/activate # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Start Frontend SPA Client
npm install
npm run dev
```

## 📜 License
Licensed under the [MIT License](LICENSE).
"""


global_readme_generator = ReadmeGenerator()
