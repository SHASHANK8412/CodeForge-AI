"""
Project templates: the stack and file layout a generation targets.

A template is chosen before generation (POST /api/generations {"template": ...}). It drives:
  * the code agents' prompts (stack + layout contract, backend/services/prompt_builder.py),
  * deterministic configuration files written at assembly when the agents did not write them
    (.gitignore, .env.example, ...), never overwriting generated files,
  * the required-file check reported at the final review (missing files are listed, not faked).
"""

from typing import Any, Dict, List, Optional

GITIGNORE = """# dependencies and builds
node_modules/
.venv/
venv/
__pycache__/
dist/
build/
.next/
# local environment and data
.env
.env.*
!.env.example
*.db
*.sqlite3
"""

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "fastapi-react": {
        "label": "FastAPI + React",
        "description": "Python FastAPI REST API with SQLAlchemy, and a React (Vite) single-page app.",
        "stack": {"backend": "FastAPI (Python)", "frontend": "React + Vite", "database": "SQLite via SQLAlchemy"},
        "backend_layout": (
            "- backend/main.py defines `app = FastAPI(...)`, adds CORS for http://localhost:5173, and has "
            "GET /health returning {\"status\": \"ok\"}\n"
            "- other backend modules live in backend/ and are imported as `from backend.<module> import ...`; "
            "backend/__init__.py exists\n"
            "- ORM models in backend/models.py, the engine/session in backend/database.py (SQLAlchemy, "
            "DATABASE_URL from the environment, default sqlite:///./app.db), schemas in backend/schemas.py\n"
            "- requirements.txt at the project root lists every third-party package imported\n"
            "- import only standard-library modules, packages in requirements.txt, and files you write here"
        ),
        "frontend_layout": (
            "- frontend/package.json (react, react-dom, vite, @vitejs/plugin-react; scripts dev/build), "
            "frontend/index.html, frontend/vite.config.js, frontend/src/main.jsx, frontend/src/App.jsx, "
            "components in frontend/src/components/\n"
            "- the API base URL is `import.meta.env.VITE_API_URL || 'http://localhost:8000'`\n"
            "- only call the API endpoints listed above; handle loading and error states"
        ),
        "test_instructions": "Write pytest tests. Import the app with `from backend.main import app` and use "
                             "`fastapi.testclient.TestClient`.",
        "required_files": ["backend/main.py", "requirements.txt", "frontend/package.json", "frontend/src/App.jsx"],
        "scaffold": {
            ".gitignore": GITIGNORE,
            ".env.example": "DATABASE_URL=sqlite:///./app.db\nVITE_API_URL=http://localhost:8000\n",
            "backend/__init__.py": "",
        },
    },
    "mern": {
        "label": "MERN",
        "description": "Node.js Express API with MongoDB (Mongoose) and a React (Vite) frontend.",
        "stack": {"backend": "Express (Node.js)", "frontend": "React + Vite", "database": "MongoDB via Mongoose"},
        "backend_layout": (
            "- this is a Node.js backend, not Python: backend/package.json (express, mongoose, cors, dotenv; "
            "\"type\": \"module\"; scripts start and test using `node --test`)\n"
            "- backend/src/app.js creates and exports the Express app (CORS for http://localhost:5173, "
            "GET /health returning {\"status\": \"ok\"}); backend/src/server.js connects to "
            "process.env.MONGODB_URI and listens on process.env.PORT || 8000\n"
            "- Mongoose models in backend/src/models/, routers in backend/src/routes/\n"
            "- import only Node built-ins, packages in backend/package.json, and files you write here"
        ),
        "frontend_layout": (
            "- frontend/package.json (react, react-dom, vite, @vitejs/plugin-react; scripts dev/build), "
            "frontend/index.html, frontend/src/main.jsx, frontend/src/App.jsx, components in frontend/src/components/\n"
            "- the API base URL is `import.meta.env.VITE_API_URL || 'http://localhost:8000'`\n"
            "- only call the API endpoints listed above"
        ),
        "test_instructions": "Write tests with the Node.js built-in test runner (`node:test`, `node:assert`) in "
                             "backend/test/*.test.js that import the app from ../src/app.js and call it over HTTP "
                             "on an ephemeral port. Do not require a running MongoDB.",
        "required_files": ["backend/package.json", "backend/src/app.js", "backend/src/server.js",
                           "frontend/package.json", "frontend/src/App.jsx"],
        "scaffold": {
            ".gitignore": GITIGNORE,
            ".env.example": "MONGODB_URI=mongodb://localhost:27017/app\nPORT=8000\nVITE_API_URL=http://localhost:8000\n",
        },
    },
    "nextjs": {
        "label": "Next.js",
        "description": "A single Next.js (App Router) app: React pages and API route handlers.",
        "stack": {"backend": "Next.js route handlers", "frontend": "Next.js (React, App Router)", "database": "SQLite via Prisma"},
        "backend_layout": (
            "- this is a Next.js App Router project at the project root, not Python: package.json (next, react, "
            "react-dom; scripts dev/build/start/test), next.config.mjs\n"
            "- API endpoints are route handlers in app/api/<name>/route.js exporting GET/POST/... functions; "
            "include app/api/health/route.js returning {\"status\": \"ok\"}\n"
            "- data access in lib/db.js (Prisma client; prisma/schema.prisma with the SQLite datasource "
            "env(\"DATABASE_URL\"))\n"
            "- import only packages in package.json and files you write here"
        ),
        "frontend_layout": (
            "- pages and layouts in app/ (app/layout.js, app/page.js, more under app/<route>/page.js), shared "
            "components in components/\n"
            "- call the API with relative URLs (/api/...), only the endpoints listed above"
        ),
        "test_instructions": "Write tests with the Node.js built-in test runner (`node:test`) in tests/*.test.js "
                             "for the pure functions in lib/ (route handlers can be called directly with a Request).",
        "required_files": ["package.json", "app/layout.js", "app/page.js", "app/api/health/route.js"],
        "scaffold": {
            ".gitignore": GITIGNORE,
            ".env.example": "DATABASE_URL=file:./dev.db\n",
        },
    },
}

DEFAULT_TEMPLATE = "fastapi-react"


def get_template(template_id: Optional[str]) -> Dict[str, Any]:
    return TEMPLATES[template_id if template_id in TEMPLATES else DEFAULT_TEMPLATE]


def list_templates() -> List[Dict[str, Any]]:
    return [{"id": tid, "label": t["label"], "description": t["description"], "stack": t["stack"],
             "required_files": t["required_files"]} for tid, t in TEMPLATES.items()]


def apply_scaffold(template_id: Optional[str], files: Dict[str, str]) -> Dict[str, str]:
    """The template's config files that the agents did not write (generated files win)."""
    return {path: content for path, content in get_template(template_id)["scaffold"].items() if path not in files}


def missing_required_files(template_id: Optional[str], files: Dict[str, str]) -> List[str]:
    return [path for path in get_template(template_id)["required_files"] if path not in files]
