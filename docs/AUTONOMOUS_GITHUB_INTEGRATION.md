# AIForge Autonomous GitHub Integration

The **AIForge Autonomous GitHub Integration** allows AIForge to automatically publish validated, generated projects directly to GitHub through an autonomous, secure pipeline.

---

## 1. Architectural Workflow

```
Project Generated
   │
   ▼
[ Docker / Local Validation ]
   │
   ▼
[ Multi-Stage CI/CD Pipeline ]
   │
   ▼
[ Pre-Publish Secret Scan ]  ───(Secrets Found)──►  ABORT & REPORT
   │ (Clean)
   ▼
[ Initialize Local Git (main) ]
   │
   ▼
[ Auto-Generate .gitignore ]
   │
   ▼
[ Auto-Generate README.md ]
   │
   ▼
[ Auto-Generate .github/workflows/aiforge-ci.yml ]
   │
   ▼
[ Safe Staging & Structured Commit ("feat: generate project") ]
   │
   ▼
[ Create GitHub Remote Repository (Private by Default) ]
   │
   ▼
[ Configure Remote (origin) ]
   │
   ▼
[ Push Default Branch (main) ]
   │
   ▼
[ Persist Repository Metadata ]
   │
   ▼
Return Structured Result (status="published", URL, Commit SHA)
```

---

## 2. Core Modules

### 1. Git Service Abstraction (`backend/github/git_service.py`)
* Safe CLI execution via `subprocess.run(["git", ...], shell=False)` to prevent shell injection.
* Automatic branch sanitization (`sanitize_branch_name`), eliminating illegal characters, control sequences, and trailing slashes.
* Core commands: `init`, `status`, `add`, `commit`, `branch`, `remote_add`, `remote_get`, and `push`.
* Sets `GIT_TERMINAL_PROMPT=0` and `GIT_ASKPASS=echo` to prevent terminal hanging.

### 2. GitHub REST API v3 Service (`backend/github/github_api_service.py`)
* Communicates directly with the official GitHub REST API v3.
* Endpoint operations:
  * Authentication verification (`GET /user`)
  * Rate limit checking (`GET /rate_limit`)
  * Repository creation (`POST /user/repos` or `POST /orgs/{org}/repos`)
  * Repository metadata query (`GET /repos/{owner}/{repo}`)
* Typed error hierarchy:
  * `GitHubAuthError` (HTTP 401)
  * `GitHubRepoExistsError` (HTTP 422 / 409)
  * `GitHubRateLimitError` (HTTP 403 / 429)
  * `GitHubAPIError` (General API errors)
* Offline mock/simulation fallback when no token is present.

### 3. Pre-Publish Security Scanner & Secret Protection
Before staging any file, `AutonomousGitHubPublisher` executes a regex-based scan for sensitive credentials:
* AWS Access Keys (`AKIA...`)
* GitHub Personal Access Tokens (`ghp_...`, `github_pat_...`)
* Private Keys (`-----BEGIN RSA/EC/OPENSSH PRIVATE KEY-----`)
* Hardcoded API keys (`api_key = "..."`)
* Automatically excludes `.env`, `*.key`, and secret files from the workspace and commits.
* If a potential secret is detected in project code, publishing is immediately aborted with a `SecurityViolationError`.

### 4. Automatic File Generation
* **`.gitignore`**: Excludes secrets (`.env`, `*.key`, `secrets/`), Python artifacts (`__pycache__`, `.venv`, `.pytest_cache`), Node artifacts (`node_modules`, `dist`), and IDE settings (`.idea`, `.vscode`).
* **`README.md`**: Generated using `DocumentationAgent` / enriched templates containing project overview, tech stack, architecture, installation, build, running tests, and CI/CD instructions.
* **`.github/workflows/aiforge-ci.yml`**: Generated dynamically based on detected technology stack (Python vs Node.js/React).

### 5. Repository Metadata Persistence (`backend/github/repo_store.py`)
Stores project GitHub linkages:
* `project_id`
* `github_repo_id`
* `repo_name`
* `repo_url`
* `owner`
* `default_branch`
* `visibility`
* `last_commit_sha`
* `last_sync_time`
* `status`
* Persisted in `logs/github_repositories.json` and mirrored in the `github_repositories` database table.
* **Tokens are never stored in plaintext database fields.**

---

## 3. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/github/connect` | Verifies GitHub authentication credentials and checks rate limits |
| `POST` | `/api/github/repository` | Creates a new repository on GitHub (private by default) |
| `POST` | `/api/github/publish` | Full autonomous publishing workflow (scan, init, commit, push, return URL) |
| `GET` | `/api/github/repository/{project_id}` | Retrieves connected repository metadata and sync status |
| `POST` | `/api/github/sync` | Pushes subsequent patches and updates with structured commit message |
| `POST` | `/api/github/git-init` | Initializes local Git repository |
| `GET` | `/api/github/git-status` | Returns local Git status (branch, clean/dirty, staged) |
| `POST` | `/api/github/commit` | Safe staging and local commit |
| `POST` | `/api/github/branch` | Creates and checkouts sanitized feature branch |
| `POST` | `/api/github/push` | Pushes local commits to remote |
| `GET` | `/api/github/overview` | Retrieves PR dashboard and active branch status |

---

## 4. Structured Publish Response

Upon successful publishing, the API returns:

```json
{
  "status": "published",
  "repository": {
    "name": "aiforge-ecommerce-api",
    "url": "https://github.com/SHASHANK8412/aiforge-ecommerce-api",
    "visibility": "private",
    "branch": "main"
  },
  "commit": {
    "sha": "9af8c96",
    "message": "feat: generate project"
  },
  "ci": {
    "workflow_created": true
  },
  "duration": 2.45
}
```

---

## 5. Frontend UI Dashboard

Located under **Engineering Suite -> GitHub Integration** (`/github`):
* **Connection Status**: Real-time display (✅ Connected / Disconnected).
* **Repository Details**: Remote name, default branch (`main`), visibility (`Private` / `Public`).
* **Publish Action**: One-click "Publish to GitHub" button with real-time feedback.
* **Direct Repository Link**: `[Open GitHub Repository]` button opens the live GitHub page.
* **Latest Commit Tracker**: Displays commit message and short SHA badge.
* **Incremental Sync Button**: Pushes subsequent code changes and patches.
* **Security & Error Banners**: Highlights rate limits, authentication errors, or leaked secret detections.

---

## 6. Troubleshooting

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| `SECURITY_VIOLATION` | Leaked API key or private token found in code | Remove credentials from project code and store them in environment variables. |
| `HTTP 401 Bad credentials` | Invalid `GITHUB_TOKEN` | Verify token scopes (`repo`, `workflow`) in GitHub Settings. |
| `HTTP 409 Repository already exists` | Repository name already exists on account | Choose a unique repository name or delete the existing remote repo. |
| `HTTP 429 Rate limit exceeded` | GitHub API rate limit reached | Wait until reset window or configure an authenticated GitHub token with higher rate quotas (5000 req/hr). |
