/**
 * frontend/src/services/memory.js
 * =================================
 * API service for project memory, architectural decisions, and decision explainability.
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
      'Content-Type': 'application/json',
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

/**
 * Fetch project memories and architectural decisions.
 */
export async function fetchProjectMemory(projectId) {
  return _apiFetch(`/api/projects/${projectId}/memory`);
}

/**
 * Search project memory using natural language query.
 */
export async function searchProjectMemory(projectId, query) {
  return _apiFetch(`/api/projects/${projectId}/memory/search`, {
    method: 'POST',
    body: JSON.stringify({ query, top_k: 8 }),
  });
}

/**
 * Delete a specific memory item.
 */
export async function deleteProjectMemory(projectId, memoryId) {
  return _apiFetch(`/api/projects/${projectId}/memory/${memoryId}`, {
    method: 'DELETE',
  });
}

/**
 * Request explainability on an architectural choice.
 */
export async function explainDecision(projectId, topic) {
  return _apiFetch(`/api/projects/${projectId}/explain?topic=${encodeURIComponent(topic)}`);
}
