import logging

_logger = logging.getLogger("aiforge.performance")


class ReadmeGenerator:
    """
    Programmatically builds a comprehensive, beautiful README.md documentation
    file for the generated software project.
    """

    def __init__(self) -> None:
        pass

    def generate_readme(self, project_name: str, state: dict) -> str:
        """
        Creates the README markdown contents using the project details.
        """
        _logger.info("Generating README.md documentation...")

        # Extract specifications to include in architecture/overview
        plan = state.get("plan", "No plan specified.")
        architecture = state.get("architecture", "No architecture document specified.")
        
        # Read the first few lines of plan and architecture for overview
        plan_snippet = "\n".join(plan.splitlines()[:15])
        arch_snippet = "\n".join(architecture.splitlines()[:15])

        readme = f"""# {project_name}

Generated autonomously with 🚀 **AIForge** - Multi-Agent AI Software Engineering Platform.

---

## 📋 Project Overview
This is a production-ready, containerized full-stack application built using **React** for the frontend interface and **FastAPI** for the backend logic and services.

### Core Features
- Complete user layout interface using React and modern CSS styling.
- RESTful API controllers with automatic document models using FastAPI.
- Robust database persistence mapping.
- Pytest testing suite coverage checking.

---

## 🏗️ System Architecture
The application runs on a decoupled, parallel layout structured as follows:
- **Frontend App**: SPA built with React and bundled via Vite.
- **Backend App**: REST API service built with FastAPI.
- **Database Layer**: Structured schema matching model requirements.

```
                  ┌─────────────────┐
                  │   Web Browser   │
                  └────────┬────────┘
                           │ HTTP Request
                           ▼
                  ┌─────────────────┐
                  │ React SPA (80)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ FastAPI (8000)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Database Layer │
                  └─────────────────┘
```

### Plan Snippet
```markdown
{plan_snippet}
...
```

### Architecture Snippet
```markdown
{arch_snippet}
...
```

---

## 📁 Folder Structure
```text
{project_name}/
├── frontend/             # React Vite SPA Source
│   ├── src/
│   │   ├── components/   # Shared layout elements
│   │   └── App.jsx       # Main App view routing
│   ├── package.json      # NPM dependencies configuration
│   └── Dockerfile        # Production nginx configuration
│
├── backend/              # FastAPI Application Source
│   ├── main.py           # App routing entry point
│   ├── requirements.txt  # Python pip dependencies
│   └── Dockerfile        # Backend service deployment
│
├── database/             # Relational Database persistence
│   └── schema.sql        # Table structures initialization script
│
├── tests/                # Testing suite folder
│   └── test_app.py       # Automated testing scripts
│
├── docker-compose.yml    # Main stack container setup orchestration
├── .env.example          # Environment variables template
└── README.md             # This instruction documentation
```

---

## ⚙️ Installation & Running

### Option 1: Running with Docker Compose (Recommended)
Make sure you have Docker installed on your host machine, then run:

```bash
# 1. Build and run all services in the background
docker compose up --build -d

# 2. View streaming logs
docker compose logs -f
```
The Frontend will be accessible at: `http://localhost:80`
The Backend API documentation will be accessible at: `http://localhost:8000/docs`

---

### Option 2: Running Locally

#### 1. Setup Backend
Ensure python 3.10+ is installed on your host:

```bash
cd backend
python -m venv .venv
# On Windows
.venv\\Scripts\\activate
# On macOS/Linux
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run server
uvicorn backend.main:app --reload --port 8000
```

#### 2. Setup Frontend
Ensure Node.js 18+ is installed on your host:

```bash
cd frontend
npm install
npm run dev
```
The local Vite server will boot at: `http://localhost:5173`

---

## 🔒 Environment Variables
Copy `.env.example` to `.env` in the root folder and configure:
- `PORT`: Port server key
- `DATABASE_URL`: Connection string URL
- `JWT_SECRET`: Authorization encryption key
- `OLLAMA_MODEL`: Target LLM model name

---

## 🧪 Testing
To execute backend testing suites locally:

```bash
cd backend
pytest tests/
```

---

## 📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
"""
        _logger.info("README.md generated successfully")
        return readme
