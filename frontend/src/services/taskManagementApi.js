/**
 * AIForge Task Management API Service
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const LOCAL_KEY = "aiforge_tasks_local_store";

const INITIAL_TASKS = [
  {
    id: "task_food_01",
    title: "Implement Redis Streams Courier Geolocation Queue",
    description: "Build high-throughput async ingest worker for real-time driver coordinate broadcasts.",
    priority: "CRITICAL",
    status: "IN_PROGRESS",
    deadline: "Tomorrow, 5:00 PM",
    project_id: "aiforge-fooddelivery-ai",
    assigned_agent: "agent-coding",
    dependencies: [],
    tags: ["Backend", "Redis", "FastAPI"]
  },
  {
    id: "task_food_02",
    title: "Design Dynamic Surge Pricing Estimation Model",
    description: "Analyze dinner peak order volume and compute dynamic delivery fee multiplier.",
    priority: "HIGH",
    status: "TODO",
    deadline: "In 3 Days",
    project_id: "aiforge-fooddelivery-ai",
    assigned_agent: "agent-data-analyst",
    dependencies: ["task_food_01"],
    tags: ["Analytics", "Pricing", "Algorithms"]
  },
  {
    id: "task_food_03",
    title: "Comprehensive DBMS Indexing & Normalization Study Plan",
    description: "Complete 5-day syllabus revision for B-Trees, transactions, and ACID isolation levels.",
    priority: "HIGH",
    status: "DONE",
    deadline: "Completed",
    project_id: "aiforge-fooddelivery-ai",
    assigned_agent: "agent-study",
    dependencies: [],
    tags: ["Study", "DBMS", "Exam"]
  },
  {
    id: "task_food_04",
    title: "Stripe Webhook & RS256 Idempotency Review",
    description: "Verify idempotency keys and replay protection for customer checkout transactions.",
    priority: "MEDIUM",
    status: "REVIEW",
    deadline: "Friday, 12:00 PM",
    project_id: "aiforge-fooddelivery-ai",
    assigned_agent: "agent-coding",
    dependencies: [],
    tags: ["Security", "Payments", "Audit"]
  }
];

function getLocalTasks() {
  try {
    const raw = localStorage.getItem(LOCAL_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_KEY, JSON.stringify(INITIAL_TASKS));
      return INITIAL_TASKS;
    }
    return JSON.parse(raw);
  } catch (e) {
    return INITIAL_TASKS;
  }
}

function saveLocalTasks(tasks) {
  try {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(tasks));
  } catch (e) {}
}

export async function fetchTasks({ projectId, status } = {}) {
  try {
    const res = await axios.get(`${API_BASE}/api/tasks`, { params: { project_id: projectId, status }, timeout: 4000 });
    if (res.data?.tasks) {
      saveLocalTasks(res.data.tasks);
      return res.data.tasks;
    }
  } catch (err) {
    console.warn("Local fallback for fetchTasks:", err);
  }
  let tasks = getLocalTasks();
  if (projectId) tasks = tasks.filter(t => t.project_id === projectId);
  if (status && status !== "ALL") tasks = tasks.filter(t => t.status === status);
  return tasks;
}

export async function createTask(payload) {
  try {
    const res = await axios.post(`${API_BASE}/api/tasks`, payload, { timeout: 5000 });
    if (res.data?.task) {
      const current = getLocalTasks();
      saveLocalTasks([res.data.task, ...current]);
      return res.data.task;
    }
  } catch (err) {
    console.warn("Local fallback for createTask:", err);
  }
  const newTask = {
    id: `task_${Date.now()}`,
    ...payload,
    created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
    updated_at: new Date().toISOString().slice(0, 19).replace("T", " ")
  };
  const current = getLocalTasks();
  saveLocalTasks([newTask, ...current]);
  return newTask;
}

export async function updateTask(taskId, payload) {
  try {
    const res = await axios.put(`${API_BASE}/api/tasks/${taskId}`, payload, { timeout: 5000 });
    if (res.data?.task) {
      const current = getLocalTasks();
      saveLocalTasks(current.map(t => t.id === taskId ? res.data.task : t));
      return res.data.task;
    }
  } catch (err) {
    console.warn("Local fallback for updateTask:", err);
  }
  const current = getLocalTasks();
  const updated = current.map(t => t.id === taskId ? { ...t, ...payload, updated_at: new Date().toISOString().slice(0, 19).replace("T", " ") } : t);
  saveLocalTasks(updated);
  return updated.find(t => t.id === taskId);
}

export async function deleteTask(taskId) {
  try {
    await axios.delete(`${API_BASE}/api/tasks/${taskId}`, { timeout: 4000 });
  } catch (err) {}
  const current = getLocalTasks();
  saveLocalTasks(current.filter(t => t.id !== taskId));
  return true;
}

export async function decomposeGoal(goal, projectId = "aiforge-fooddelivery-ai") {
  try {
    const res = await axios.post(`${API_BASE}/api/tasks/decompose`, { goal, project_id: projectId }, { timeout: 6000 });
    if (res.data?.decomposed_tasks) {
      const current = getLocalTasks();
      saveLocalTasks([...res.data.decomposed_tasks, ...current]);
      return res.data.decomposed_tasks;
    }
  } catch (err) {
    console.warn("Local fallback for decomposeGoal:", err);
  }
  const fallbackTasks = [
    { title: `Phase 1: Architecture Plan for ${goal.slice(0, 30)}`, priority: "HIGH", status: "TODO", assigned_agent: "agent-coding", project_id: projectId },
    { title: `Phase 2: Core Implementation & Schema`, priority: "HIGH", status: "TODO", assigned_agent: "agent-coding", project_id: projectId },
    { title: `Phase 3: Integration Tests & Verification`, priority: "MEDIUM", status: "TODO", assigned_agent: "agent-coding", project_id: projectId }
  ];
  const created = [];
  for (const f of fallbackTasks) {
    created.push(await createTask(f));
  }
  return created;
}

export async function fetchNextBestAction(projectId = "aiforge-fooddelivery-ai") {
  try {
    const res = await axios.get(`${API_BASE}/api/tasks/next-best-action`, { params: { project_id: projectId }, timeout: 4000 });
    if (res.data?.action) {
      return res.data.action;
    }
  } catch (err) {}
  return {
    recommendation: "Continue In-Progress Task: Implement Redis Streams Courier Geolocation Queue",
    reason: "Highest priority active backend infrastructure item.",
    suggested_action: "Dispatch Coding Agent or open Code Workspace."
  };
}
