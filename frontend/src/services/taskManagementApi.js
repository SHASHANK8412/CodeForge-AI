import { BACKEND_URL } from '../config/backend';
/**
 * AIForge Task API Service
 * ========================
 * The signed-in user's tasks, stored by the backend. Errors are thrown to the caller;
 * nothing is invented when the backend cannot be reached.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;

export async function fetchTasks({ projectId, status } = {}) {
  const res = await axios.get(`${API_BASE}/api/tasks`, { params: { project_id: projectId, status }, timeout: 4000 });
  return res.data?.tasks || [];
}

export async function createTask(payload) {
  const res = await axios.post(`${API_BASE}/api/tasks`, payload, { timeout: 5000 });
  return res.data?.task || null;
}

export async function updateTask(taskId, payload) {
  const res = await axios.put(`${API_BASE}/api/tasks/${taskId}`, payload, { timeout: 5000 });
  return res.data?.task || null;
}

export async function deleteTask(taskId) {
  await axios.delete(`${API_BASE}/api/tasks/${taskId}`, { timeout: 4000 });
  return true;
}

export async function fetchNextBestAction(projectId) {
  const res = await axios.get(`${API_BASE}/api/tasks/next-best-action`, { params: { project_id: projectId }, timeout: 4000 });
  return res.data?.action || null;
}
