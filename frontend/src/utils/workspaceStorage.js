// Utility to manage saved AI outputs, activity log, and recommendations
const SAVED_OUTPUTS_KEY = "aiforge_saved_outputs";
const ACTIVITY_LOG_KEY = "aiforge_activity_log";

const INITIAL_SAVED_OUTPUTS = [
  {
    id: "out-1",
    title: "FastAPI JWT Authentication & Rate Limiting Middleware",
    category: "Coding",
    type: "code",
    language: "python",
    tags: ["FastAPI", "Security", "JWT", "Middleware"],
    created_at: "2 hours ago",
    summary: "Production-ready async JWT verification and token bucket rate limiter for FastAPI endpoints.",
    content: `from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

security = HTTPBearer()
SECRET_KEY = "aiforge-super-secret-production-key"
ALGORITHM = "HS256"

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")`
  },
  {
    id: "out-2",
    title: "Microservices Architecture Specification (RFC-104)",
    category: "Writing",
    type: "architecture",
    language: "markdown",
    tags: ["Architecture", "System Design", "Microservices", "Event-Driven"],
    created_at: "Yesterday",
    summary: "Event-driven system design with Kafka event broker, PostgreSQL write-models, and Elasticsearch read-models.",
    content: `# RFC-104: Event-Driven Order Processing Engine

## 1. System Overview
- **Ingress Gateway**: Cloudflare Edge + Envoy API Gateway
- **Auth Provider**: Decentralized JWT with RS256 signing
- **Event Bus**: Apache Kafka / Redpanda with Avro schema registry
- **State Store**: PostgreSQL (ACID Write-Model) & Redis (Cache)
- **Search & Analytics**: OpenSearch cluster for real-time telemetry`
  },
  {
    id: "out-3",
    title: "Multi-Agent Consensus & Debate Evaluation Prompt",
    category: "Research",
    type: "prompt",
    language: "text",
    tags: ["Prompts", "Multi-Agent", "Consensus", "Evaluation"],
    created_at: "3 days ago",
    summary: "High-accuracy dual-agent verification prompt for SAST security analysis and algorithmic time complexity audit.",
    content: `You are the Lead Verification Judge in a multi-agent debate.
Evaluate the code proposed by Agent A (Speed-Optimized) vs Agent B (Memory-Optimized).
1. Prove time complexity $O(N)$ vs $O(N \log N)$ empirically.
2. Identify edge cases (empty collections, concurrency races, integer overflows).
3. Synthesize a unified optimal implementation with zero performance compromises.`
  },
  {
    id: "out-4",
    title: "Docker Multi-Stage Production Build Optimization",
    category: "Productivity",
    type: "code",
    language: "dockerfile",
    tags: ["Docker", "DevOps", "CI/CD", "Optimization"],
    created_at: "5 days ago",
    summary: "Ultra-lean 42MB Alpine container image for React + Vite static bundle served via Nginx with Brotli compression.",
    content: `# Stage 1: Build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine-slim
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]`
  }
];

const INITIAL_ACTIVITIES = [
  {
    id: "act-1",
    title: "FoodDelivery AI Engine Generated",
    type: "project",
    status: "success",
    timestamp: "10 mins ago",
    description: "48/48 unit & integration tests passed. Deployed to edge runner.",
    actionLink: "code",
    actionLabel: "Open Workspace"
  },
  {
    id: "act-2",
    title: "Deep Security SAST Audit Completed",
    type: "security",
    status: "success",
    timestamp: "45 mins ago",
    description: "Reviewer Agent scanned 14 modules. 0 critical vulnerabilities found.",
    actionLink: "security",
    actionLabel: "View Audit"
  },
  {
    id: "act-3",
    title: "Multi-Agent Debate Arena Session",
    type: "debate",
    status: "info",
    timestamp: "2 hours ago",
    description: "Architect Agent & Security Agent debated database connection pool sizing.",
    actionLink: "debate",
    actionLabel: "View Debate"
  },
  {
    id: "act-4",
    title: "DNA Dependency Graph Indexed",
    type: "dna",
    status: "success",
    timestamp: "Yesterday",
    description: "Parsed 128 AST symbols and mapped inter-module dependency topology.",
    actionLink: "dna",
    actionLabel: "Explore DNA"
  },
  {
    id: "act-5",
    title: "Autopilot Flight Mission #42",
    type: "autopilot",
    status: "success",
    timestamp: "2 days ago",
    description: "Automated refactoring loop resolved 6 typing warnings in backend routers.",
    actionLink: "autopilot",
    actionLabel: "Flight Logs"
  }
];

export function getSavedOutputs() {
  try {
    const raw = localStorage.getItem(SAVED_OUTPUTS_KEY);
    if (!raw) {
      localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(INITIAL_SAVED_OUTPUTS));
      return INITIAL_SAVED_OUTPUTS;
    }
    return JSON.parse(raw);
  } catch (err) {
    console.error("Error reading saved outputs from localStorage:", err);
    return INITIAL_SAVED_OUTPUTS;
  }
}

export function saveOutputItem(item) {
  try {
    const current = getSavedOutputs();
    const newItem = {
      id: `out-${Date.now()}`,
      created_at: "Just now",
      ...item
    };
    const updated = [newItem, ...current];
    localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent("aiforge:saved-outputs-updated", { detail: { outputs: updated } }));
    return newItem;
  } catch (err) {
    console.error("Error saving output item:", err);
    return null;
  }
}

export function deleteSavedOutputItem(id) {
  try {
    const current = getSavedOutputs();
    const updated = current.filter(item => item.id !== id);
    localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent("aiforge:saved-outputs-updated", { detail: { outputs: updated } }));
    return true;
  } catch (err) {
    console.error("Error deleting saved output:", err);
    return false;
  }
}

export function getActivityLog() {
  try {
    const raw = localStorage.getItem(ACTIVITY_LOG_KEY);
    if (!raw) {
      localStorage.setItem(ACTIVITY_LOG_KEY, JSON.stringify(INITIAL_ACTIVITIES));
      return INITIAL_ACTIVITIES;
    }
    return JSON.parse(raw);
  } catch (err) {
    console.error("Error reading activity log:", err);
    return INITIAL_ACTIVITIES;
  }
}

export function logActivity(activity) {
  try {
    const current = getActivityLog();
    const newAct = {
      id: `act-${Date.now()}`,
      timestamp: "Just now",
      status: "success",
      ...activity
    };
    const updated = [newAct, ...current.slice(0, 49)];
    localStorage.setItem(ACTIVITY_LOG_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent("aiforge:activity-logged", { detail: { activity: newAct } }));
    return newAct;
  } catch (err) {
    console.error("Error logging activity:", err);
    return null;
  }
}
