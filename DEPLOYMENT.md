# Deploying AIForge

## Docker Compose (single machine)

```bash
cp .env.example .env               # optional; compose works without it
docker compose up --build -d
```

| Service | URL |
|---|---|
| Frontend (nginx) | http://localhost:8080 |
| Backend API | http://localhost:8000 (health: `/health`, docs: `/docs`) |

The backend calls the Ollama running on the **host** by default (`OLLAMA_HOST=http://host.docker.internal:11434`).
To run Ollama in a container instead:

```bash
OLLAMA_HOST=http://ollama:11434 docker compose --profile ollama up --build -d
docker compose exec ollama ollama pull llama3.2:3b
```

Generated projects (`generated-projects`), JSON stores (`backend-data`) and the SQLite database
(`backend-database`) live in named volumes and survive `docker compose down` (not `down -v`).

## Frontend and backend on separate hosts

The frontend is a static Vite build; the backend is a FastAPI service.

1. **Backend** — build `backend/Dockerfile` (context: repository root) and run it anywhere that
   can reach an Ollama endpoint. Set:
   - `OLLAMA_HOST` — URL of your Ollama server. Most free hosting tiers cannot run Ollama
     themselves, so this usually points at a separate GPU machine.
   - `CORS_ORIGINS` — the frontend's public URL, e.g. `https://aiforge.example.com`.
   - `JWT_SECRET` and, if not using SQLite, `DATABASE_URL`.
2. **Frontend** — build with the backend's public URL baked in:
   ```bash
   cd frontend
   VITE_API_URL=https://api.aiforge.example.com npm run build
   ```
   and serve `frontend/dist/` from any static host (Vercel, Netlify, S3 + CloudFront, nginx).
   It is a single-page app: route unknown paths to `index.html` (see `frontend/nginx.conf`).

## Deploying projects that AIForge generates

The Vercel / Render / Neon providers in `backend/deployment/providers/` generate deployment
configuration (`vercel.json`, `render.yaml`, …) for a generated project, but **do not call those
platforms' APIs yet**. A deploy request returns `NOT_CONFIGURED` when the provider's token
(`VERCEL_TOKEN`, `RENDER_API_KEY`, `NEON_API_KEY`) is missing and `MANUAL_DEPLOY_REQUIRED` with
instructions when it is set; it never reports a URL for a deployment that did not happen.
