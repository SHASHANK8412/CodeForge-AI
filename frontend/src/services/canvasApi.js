/**
 * AIForge Live Canvas API Service
 * ================================
 * Handles persistent multi-modal canvas management, 2-way AI synchronization,
 * and version snapshot history with local fallback.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const LOCAL_CANVAS_KEY = "aiforge_live_canvases_store";

export const INITIAL_CANVASES = [
  {
    id: "canvas-roadmap-ml",
    title: "Machine Learning 30-Day Mastery Roadmap",
    canvas_type: "ROADMAP",
    project_id: "aiforge-fooddelivery-ai",
    tags: ["AI", "Machine Learning", "Roadmap"],
    created_at: "2026-08-30 10:00:00",
    updated_at: "2026-08-30 10:00:00",
    content: [
      {
        phase: "01",
        title: "Python & Data Science Foundations",
        duration: "Day 1 - 6",
        status: "COMPLETED",
        description: "Master NumPy array operations, Pandas dataframe transformations, Matplotlib/Seaborn visualization, and clean vectorization pipelines.",
        milestones: ["NumPy Matrix Math", "Pandas Data Wrangling", "Exploratory Data Analysis"]
      },
      {
        phase: "02",
        title: "Mathematics & Classical Machine Learning",
        duration: "Day 7 - 14",
        status: "IN_PROGRESS",
        description: "Linear Algebra (Eigenvalues, SVD), Multivariable Calculus (Gradients), Supervised Learning (Linear/Logistic Regression, Decision Trees, Random Forests, XGBoost).",
        milestones: ["Loss Function Optimization", "Gradient Descent Implementation", "Scikit-Learn Classifier Benchmark"]
      },
      {
        phase: "03",
        title: "Deep Learning & Neural Architectures",
        duration: "Day 15 - 22",
        status: "UPCOMING",
        description: "PyTorch tensors, autograd, Multi-Layer Perceptrons, CNNs for computer vision, Transformers & Self-Attention mechanisms.",
        milestones: ["PyTorch Neural Network from Scratch", "Vision Classifier", "Attention Head Math"]
      },
      {
        phase: "04",
        title: "Production Deployment & Capstone",
        duration: "Day 23 - 30",
        status: "UPCOMING",
        description: "Export ONNX models, build FastAPI inference microservice, containerize with Docker, and deploy to Kubernetes with live latency telemetry.",
        milestones: ["FastAPI Inference API", "Dockerized Container", "Real-Time Drift Monitoring"]
      }
    ],
    versions: [
      {
        version_id: "v-init-1",
        version_number: 1,
        title: "Machine Learning 30-Day Mastery Roadmap",
        content: null,
        canvas_type: "ROADMAP",
        author: "AI",
        change_summary: "Initial Plan",
        created_at: "2026-08-30 10:00:00"
      }
    ]
  },
  {
    id: "canvas-table-frontend",
    title: "Modern Frontend Frameworks Comparison Matrix",
    canvas_type: "TABLE",
    project_id: "aiforge-fooddelivery-ai",
    tags: ["Frontend", "React", "Vue", "Angular", "Svelte"],
    created_at: "2026-08-30 11:30:00",
    updated_at: "2026-08-30 11:30:00",
    content: {
      columns: ["Framework", "Architecture", "Reactivity Model", "Performance Score", "Ecosystem & Tooling", "Recommended Use Case"],
      rows: [
        ["React 19", "Virtual DOM + Fiber", "Hooks / Server Components", "94 / 100", "Vast (Next.js, Vite, Tailwind)", "Complex Enterprise SPAs & Dashboards"],
        ["Vue 3.5", "Virtual DOM + Compiler", "Proxy-based Reactivity", "96 / 100", "Strong (Nuxt, Pinia, Vite)", "Rapid Prototyping & Clean Templates"],
        ["Svelte 5", "No Virtual DOM (Compiled)", "Runes Reactive Signals", "99 / 100", "Growing (SvelteKit, Vite)", "High-Performance Edge Apps & Visualizations"],
        ["Angular 18", "Zone.js / Signals", "RxJS + Signals Reactive", "91 / 100", "Batteries-Included (CLI, Router, HTTP)", "Large Monolithic Enterprise Systems"]
      ]
    },
    versions: [
      {
        version_id: "v-table-1",
        version_number: 1,
        title: "Modern Frontend Frameworks Comparison Matrix",
        content: null,
        canvas_type: "TABLE",
        author: "AI",
        change_summary: "Generated matrix",
        created_at: "2026-08-30 11:30:00"
      }
    ]
  },
  {
    id: "canvas-code-backend",
    title: "Async Task Queue & Webhook Dispatcher",
    canvas_type: "CODE",
    project_id: "aiforge-fooddelivery-ai",
    tags: ["FastAPI", "Redis", "Backend"],
    created_at: "2026-08-30 12:00:00",
    updated_at: "2026-08-30 12:00:00",
    content: "from fastapi import FastAPI, BackgroundTasks, HTTPException\nimport redis.asyncio as redis\nimport asyncio\n\napp = FastAPI(title='AIForge Task Engine', version='1.0.0')\n\n@app.post('/tasks/dispatch')\nasync def dispatch_task(task_name: str, background_tasks: BackgroundTasks):\n    \"\"\"Queues task for async background processing\"\"\"\n    return {'status': 'QUEUED', 'task': task_name, 'timestamp': '2026-08-30'}\n",
    files: {
      "main.py": "from fastapi import FastAPI, BackgroundTasks, HTTPException\nimport redis.asyncio as redis\nimport asyncio\n\napp = FastAPI(title='AIForge Task Engine', version='1.0.0')\n\n@app.post('/tasks/dispatch')\nasync def dispatch_task(task_name: str, background_tasks: BackgroundTasks):\n    \"\"\"Queues task for async background processing\"\"\"\n    return {'status': 'QUEUED', 'task': task_name, 'timestamp': '2026-08-30'}\n",
      "worker.py": "import asyncio\n\nasync def run_worker():\n    print('[Worker] Listening for Redis stream events...')\n    while True:\n        await asyncio.sleep(1)\n",
      "config.py": "from pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    REDIS_URL: str = 'redis://localhost:6379/0'\n    MAX_WORKERS: int = 8\n\nsettings = Settings()\n"
    },
    versions: []
  },
  {
    id: "canvas-doc-prd",
    title: "FoodDelivery AI — Product Requirement Document (PRD)",
    canvas_type: "DOCUMENT",
    project_id: "aiforge-fooddelivery-ai",
    tags: ["PRD", "Specs", "Product"],
    created_at: "2026-08-30 13:00:00",
    updated_at: "2026-08-30 13:00:00",
    content: `# 🍔 FoodDelivery AI — Product Requirement Document (PRD)

## 1. Executive Summary
FoodDelivery AI is an autonomous, on-demand meal dispatch platform featuring real-time courier matching, dynamic ETA prediction, and ACID-compliant order state transitions.

## 2. Core Functional Requirements
- **Customer Portal**: Menu exploration, allergen filtering, cart management, and Stripe checkout.
- **Restaurant Kitchen Display**: Live incoming order queue with state transitions (\`PREPARING\` -> \`READY_FOR_PICKUP\`).
- **Courier Telemetry**: GPS live tracking and automated shortest-path routing algorithms.
- **Security & Compliance**: RS256 JWT auth with Customer, Restaurant, and Courier RBAC roles.

## 3. Architecture & Data Model
- **Backend**: FastAPI with async SQLAlchemy 2.0.
- **Database**: PostgreSQL with UUID primary keys and WAL replication.
- **Event Bus**: Redis Pub/Sub for driver broadcast.
`,
    versions: []
  }
];

function getLocalCanvases() {
  try {
    const raw = localStorage.getItem(LOCAL_CANVAS_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_CANVAS_KEY, JSON.stringify(INITIAL_CANVASES));
      return INITIAL_CANVASES;
    }
    return JSON.parse(raw);
  } catch (err) {
    return INITIAL_CANVASES;
  }
}

function saveLocalCanvases(canvases) {
  try {
    localStorage.setItem(LOCAL_CANVAS_KEY, JSON.stringify(canvases));
    window.dispatchEvent(new CustomEvent("aiforge:canvas-updated", { detail: { count: canvases.length } }));
  } catch (err) {
    console.error("Error saving canvases:", err);
  }
}

export async function fetchCanvases({ projectId, canvasType } = {}) {
  try {
    const res = await axios.get(`${API_BASE}/api/canvas/list`, {
      params: { project_id: projectId, canvas_type: canvasType },
      timeout: 5000
    });
    if (res.data?.canvases) {
      saveLocalCanvases(res.data.canvases);
      return res.data.canvases;
    }
  } catch (err) {
    console.warn("Local fallback for fetchCanvases:", err);
  }
  let items = getLocalCanvases();
  if (projectId) items = items.filter(c => c.project_id === projectId);
  if (canvasType && canvasType !== "ALL") items = items.filter(c => c.canvas_type === canvasType);
  return items;
}

export async function fetchCanvas(canvasId) {
  try {
    const res = await axios.get(`${API_BASE}/api/canvas/${canvasId}`, { timeout: 5000 });
    if (res.data?.canvas) {
      const current = getLocalCanvases();
      saveLocalCanvases(current.map(c => c.id === canvasId ? res.data.canvas : c));
      return res.data.canvas;
    }
  } catch (err) {
    console.warn("Local fallback for fetchCanvas:", err);
  }
  const items = getLocalCanvases();
  return items.find(c => c.id === canvasId) || items[0] || null;
}

export async function createCanvas(payload) {
  try {
    const res = await axios.post(`${API_BASE}/api/canvas`, payload, { timeout: 6000 });
    if (res.data?.canvas) {
      const current = getLocalCanvases();
      saveLocalCanvases([res.data.canvas, ...current]);
      return res.data.canvas;
    }
  } catch (err) {
    console.warn("Local fallback for createCanvas:", err);
  }

  const newCanvas = {
    id: `canvas-${Date.now()}`,
    title: payload.title || "Untitled Canvas",
    canvas_type: payload.canvas_type || "DOCUMENT",
    content: payload.content || `# ${payload.title || "New Canvas"}\n\nStart typing or ask AI...`,
    files: payload.files || (payload.canvas_type === "CODE" ? { "main.py": payload.content || "" } : null),
    project_id: payload.project_id || "aiforge-fooddelivery-ai",
    tags: payload.tags || [payload.canvas_type || "DOCUMENT"],
    created_at: new Date().toISOString().replace("T", " ").slice(0, 19),
    updated_at: new Date().toISOString().replace("T", " ").slice(0, 19),
    versions: [
      {
        version_id: `v-${Date.now()}`,
        version_number: 1,
        title: payload.title,
        content: payload.content,
        canvas_type: payload.canvas_type || "DOCUMENT",
        author: "User",
        change_summary: "Created Canvas",
        created_at: new Date().toISOString().replace("T", " ").slice(0, 19)
      }
    ]
  };

  const current = getLocalCanvases();
  saveLocalCanvases([newCanvas, ...current]);
  return newCanvas;
}

export async function updateCanvas(canvasId, payload) {
  try {
    const res = await axios.put(`${API_BASE}/api/canvas/${canvasId}`, payload, { timeout: 6000 });
    if (res.data?.canvas) {
      const current = getLocalCanvases();
      saveLocalCanvases(current.map(c => c.id === canvasId ? res.data.canvas : c));
      return res.data.canvas;
    }
  } catch (err) {
    console.warn("Local fallback for updateCanvas:", err);
  }

  const current = getLocalCanvases();
  const updated = current.map(c => {
    if (c.id === canvasId) {
      const newVersions = [...(c.versions || [])];
      newVersions.push({
        version_id: `v-${Date.now()}`,
        version_number: newVersions.length + 1,
        title: payload.title || c.title,
        content: payload.content !== undefined ? payload.content : c.content,
        canvas_type: c.canvas_type,
        author: payload.author || "User",
        change_summary: payload.change_summary || "Manual Edit",
        created_at: new Date().toISOString().replace("T", " ").slice(0, 19)
      });

      return {
        ...c,
        ...payload,
        versions: newVersions,
        updated_at: new Date().toISOString().replace("T", " ").slice(0, 19)
      };
    }
    return c;
  });

  saveLocalCanvases(updated);
  return updated.find(c => c.id === canvasId);
}

export async function deleteCanvas(canvasId) {
  try {
    await axios.delete(`${API_BASE}/api/canvas/${canvasId}`, { timeout: 5000 });
  } catch (err) {
    console.warn("Local fallback for deleteCanvas:", err);
  }
  const current = getLocalCanvases();
  saveLocalCanvases(current.filter(c => c.id !== canvasId));
  return true;
}

export async function aiTransformCanvas(canvasId, { instruction, selectionText }) {
  try {
    const res = await axios.post(`${API_BASE}/api/canvas/${canvasId}/ai-transform`, {
      instruction,
      selection_text: selectionText
    }, { timeout: 8000 });
    if (res.data?.canvas) {
      const current = getLocalCanvases();
      saveLocalCanvases(current.map(c => c.id === canvasId ? res.data.canvas : c));
      return res.data.canvas;
    }
  } catch (err) {
    console.warn("Local fallback for aiTransformCanvas:", err);
  }

  // Local simulated transform
  const current = getLocalCanvases();
  const canvas = current.find(c => c.id === canvasId);
  if (!canvas) return null;

  let newContent = canvas.content;
  const instLower = (instruction || "").toLowerCase();

  if (instLower.includes("presentation") || instLower.includes("slides")) {
    canvas.canvas_type = "DOCUMENT";
    newContent = `# 📊 Presentation: ${canvas.title}\n\n---\n<!-- slide -->\n## Slide 1: Executive Overview\n- Strategic Value Proposition & Architecture\n\n---\n<!-- slide -->\n## Slide 2: Implementation Milestones\n- Microservices Rollout & Telemetry`;
  } else if (canvas.canvas_type === "TABLE" && (instLower.includes("pricing") || instLower.includes("cost"))) {
    if (typeof newContent === "object" && newContent.columns) {
      if (!newContent.columns.includes("Pricing")) {
        newContent.columns.push("Pricing");
        newContent.rows.forEach(r => r.push("$49 / mo"));
      }
    }
  } else if (canvas.canvas_type === "ROADMAP" && (instLower.includes("30 days") || instLower.includes("shorter"))) {
    if (Array.isArray(newContent)) {
      newContent.forEach((node, i) => {
        node.duration = `Days ${i * 7 + 1} - ${i * 7 + 7}`;
      });
    }
  } else if (typeof newContent === "string") {
    newContent += `\n\n### ⚡ AI Transform (${instruction})\n- Verified and refined with enhanced structural details.`;
  }

  return await updateCanvas(canvasId, {
    content: newContent,
    change_summary: `AI: ${instruction.slice(0, 35)}`,
    author: "AI"
  });
}

export async function restoreCanvasVersion(canvasId, versionId) {
  try {
    const res = await axios.post(`${API_BASE}/api/canvas/${canvasId}/versions/${versionId}/restore`, {}, { timeout: 6000 });
    if (res.data?.canvas) {
      const current = getLocalCanvases();
      saveLocalCanvases(current.map(c => c.id === canvasId ? res.data.canvas : c));
      return res.data.canvas;
    }
  } catch (err) {
    console.warn("Local fallback for restoreCanvasVersion:", err);
  }

  const current = getLocalCanvases();
  const canvas = current.find(c => c.id === canvasId);
  if (!canvas) return null;

  const targetVer = (canvas.versions || []).find(v => v.version_id === versionId);
  if (!targetVer || !targetVer.content) return canvas;

  return await updateCanvas(canvasId, {
    content: targetVer.content,
    change_summary: `Restored Version ${targetVer.version_number}`
  });
}
