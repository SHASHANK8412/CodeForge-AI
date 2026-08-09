# AIForge Complete API Endpoint Map

All backend endpoints exposed by the AIForge FastAPI server (`http://127.0.0.1:8000`).

---

## 1. Authentication & Account Management (`/api/auth`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Registers a new user account & returns JWT access token | `IMPLEMENTED` |
| `POST` | `/api/auth/login` | Authenticates user & sets HTTP-Only session cookie | `IMPLEMENTED` |
| `POST` | `/api/auth/logout` | Clears authentication session & invalidates token | `IMPLEMENTED` |
| `GET` | `/api/auth/me` | Returns current authenticated user profile | `IMPLEMENTED` |
| `POST` | `/api/auth/forgot-password` | Requests password reset instructions | `IMPLEMENTED` |
| `POST` | `/api/auth/reset-password` | Updates account password using token | `IMPLEMENTED` |
| `GET` | `/api/auth/api-keys` | Lists active API keys for user | `IMPLEMENTED` |
| `POST` | `/api/auth/api-keys` | Generates new API key | `IMPLEMENTED` |
| `DELETE` | `/api/auth/api-keys/{id}` | Revokes API key | `IMPLEMENTED` |

---

## 2. System Health & Infrastructure (`/api`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System health probe (Database, Ollama LLM, LangGraph) | `IMPLEMENTED` |

---

## 3. Project Management (`/api/projects`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/projects` | Paginated list of projects belonging to current user | `IMPLEMENTED` |
| `GET` | `/api/projects/{id}` | Project details, activity history, and version list | `IMPLEMENTED` |
| `PATCH` | `/api/projects/{id}` | Renames or updates project attributes | `IMPLEMENTED` |
| `POST` | `/api/projects/{id}/duplicate` | Duplicates project into a new copy | `IMPLEMENTED` |
| `POST` | `/api/projects/{id}/archive` | Archives project | `IMPLEMENTED` |
| `DELETE` | `/api/projects/{id}` | Permanently deletes project | `IMPLEMENTED` |

---

## 4. Multi-Agent Project Generation (`/api/generate` & `/api/generations`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/generate` | Submits prompt & triggers LangGraph workflow | `IMPLEMENTED` |
| `GET` | `/api/generations/{id}` | Returns current generation state & agent statuses | `IMPLEMENTED` |
| `GET` | `/api/generations/{id}/stream` | Server-Sent Events (SSE) real-time agent log stream | `IMPLEMENTED` |

---

## 5. Code Workspace & Files (`/api/projects/{id}/files`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/projects/{id}/files` | Dynamic file tree & generated source code contents | `IMPLEMENTED` |
| `GET` | `/api/projects/{id}/download` | Downloads complete project as a `.zip` archive | `IMPLEMENTED` |

---

## 6. Quality & Evaluation (`/api/projects/{id}/quality`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/projects/{id}/quality` | Evaluates 15 Quality Gates, test results, and SAST | `IMPLEMENTED` |
| `POST` | `/api/evaluate` | Triggers self-repair engine execution | `IMPLEMENTED` |

---

## 7. DevOps & Deployment (`/api/projects/{id}/deployment`)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/projects/{id}/deployment` | Returns readiness checks, providers, and health info | `IMPLEMENTED` |
| `POST` | `/api/projects/{id}/deployment/validate` | Executes pre-deployment validation checks | `IMPLEMENTED` |
| `POST` | `/api/projects/{id}/deployment/start` | Starts production deployment workflow | `IMPLEMENTED` |
| `GET` | `/api/projects/{id}/deployment/health` | Performs live health check probe | `IMPLEMENTED` |
| `GET` | `/api/projects/{id}/deployment/stream` | SSE real-time deployment status stream | `IMPLEMENTED` |
