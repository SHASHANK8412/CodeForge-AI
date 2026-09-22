/**
 * frontend/src/services/autopilot.js
 * ===================================
 * API service for AIForge Engineering Autopilot and Engineering Flight Recorder.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function _getAuthHeader() {
  const token = localStorage.getItem('aiforge_jwt');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function _apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ..._getAuthHeader(),
      ...(opts.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {/* ignore */}
    throw new Error(detail);
  }

  return res.json();
}

export async function startAutopilot(projectId, prompt, autonomyLevel = 'BALANCED', approvalSettings = {}) {
  return _apiFetch('/api/autopilot/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: projectId,
      prompt,
      autonomy_level: autonomyLevel,
      approval_settings: approvalSettings,
    }),
  });
}

export async function fetchAutopilotState(generationId) {
  return _apiFetch(`/api/autopilot/${generationId}`);
}

export async function pauseAutopilot(generationId) {
  return _apiFetch(`/api/autopilot/${generationId}/pause`, { method: 'POST' });
}

export async function resumeAutopilot(generationId) {
  return _apiFetch(`/api/autopilot/${generationId}/resume`, { method: 'POST' });
}

export async function stopAutopilot(generationId) {
  return _apiFetch(`/api/autopilot/${generationId}/stop`, { method: 'POST' });
}

export async function approveAutopilotAction(generationId, requestId) {
  return _apiFetch(`/api/autopilot/${generationId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId }),
  });
}

export async function rejectAutopilotAction(generationId, requestId) {
  return _apiFetch(`/api/autopilot/${generationId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId }),
  });
}

export async function fetchAutopilotDecisions(generationId) {
  return _apiFetch(`/api/autopilot/${generationId}/decisions`);
}

export async function fetchFlightRecorder(projectId, filters = {}) {
  const query = new URLSearchParams(filters).toString();
  return _apiFetch(`/api/projects/${projectId}/flight-recorder${query ? `?${query}` : ''}`);
}

export async function fetchProjectAnalytics(projectId) {
  return _apiFetch(`/api/projects/${projectId}/analytics`);
}
