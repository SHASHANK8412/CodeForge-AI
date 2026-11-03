import { BACKEND_URL } from '../config/backend';
/**
 * AIForge Canvas API Service
 * ==========================
 * The signed-in user's canvases and their version history, stored by the backend.
 * Errors are thrown to the caller; nothing is invented when the backend cannot be reached.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;

function notifyChanged() {
  window.dispatchEvent(new CustomEvent("aiforge:canvas-updated"));
}

export async function fetchCanvases({ projectId, canvasType } = {}) {
  const res = await axios.get(`${API_BASE}/api/canvas/list`, {
    params: { project_id: projectId, canvas_type: canvasType },
    timeout: 5000
  });
  return res.data?.canvases || [];
}

export async function fetchCanvas(canvasId) {
  const res = await axios.get(`${API_BASE}/api/canvas/${canvasId}`, { timeout: 5000 });
  return res.data?.canvas || null;
}

export async function createCanvas(payload) {
  const res = await axios.post(`${API_BASE}/api/canvas`, payload, { timeout: 6000 });
  notifyChanged();
  return res.data?.canvas || null;
}

export async function updateCanvas(canvasId, payload) {
  const res = await axios.put(`${API_BASE}/api/canvas/${canvasId}`, payload, { timeout: 6000 });
  notifyChanged();
  return res.data?.canvas || null;
}

export async function deleteCanvas(canvasId) {
  await axios.delete(`${API_BASE}/api/canvas/${canvasId}`, { timeout: 5000 });
  notifyChanged();
  return true;
}

export async function restoreCanvasVersion(canvasId, versionId) {
  const res = await axios.post(`${API_BASE}/api/canvas/${canvasId}/versions/${versionId}/restore`, {}, { timeout: 6000 });
  notifyChanged();
  return res.data?.canvas || null;
}
