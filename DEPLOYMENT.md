# ☁️ AIForge Production Deployment Guide

## Docker Compose Deployment

### 1. Build & Start Services
```bash
docker-compose up -d --build
```

### 2. Verify Health Endpoints
- Backend API Health: `http://localhost:8000/health`
- Frontend Interface: `http://localhost:5173`

---

## Cloud Deployment (AWS / GCP / DigitalOcean)

### Backend Deployment (FastAPI + Docker)
1. Push Docker image to container registry:
   ```bash
   docker tag aiforge/backend:v1.0.0 registry.example.com/aiforge/backend:v1.0.0
   docker push registry.example.com/aiforge/backend:v1.0.0
   ```
2. Deploy to ECS / Cloud Run / Kubernetes using provided Helm charts in `docker/`.

### Frontend Deployment (React / Vite)
1. Build static production bundle:
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy `dist/` directory to Vercel / Netlify / AWS S3 + CloudFront.
