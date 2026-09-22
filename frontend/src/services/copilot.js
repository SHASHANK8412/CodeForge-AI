/**
 * frontend/src/services/copilot.js
 * ==================================
 * API service for AIForge Day 23: AI Codebase Copilot & Natural-Language Software Control:
 * - Ask Copilot
 * - Execute Plan
 * - Natural Language Code Search
 * - Fetch Copilot Session History
 * - Submit Feedback
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

export async function askCopilot(projectId = 'aiforge-demo', prompt = '', simFailure = false) {
  return _apiFetch(`/api/projects/${projectId}/copilot/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, simulate_failure: simFailure }),
  });
}

export async function executeCopilotPlan(projectId = 'aiforge-demo', planId, simFailure = false) {
  return _apiFetch(`/api/projects/${projectId}/copilot/plan/${planId}/execute?simulate_failure=${simFailure}`, {
    method: 'POST',
  });
}

export async function searchCopilotCode(projectId = 'aiforge-demo', query = '') {
  return _apiFetch(`/api/projects/${projectId}/copilot/search?q=${encodeURIComponent(query)}`);
}

export async function fetchCopilotHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/copilot/history`);
}

export async function submitCopilotFeedback(projectId = 'aiforge-demo', sessionId, messageId, rating, comment = null) {
  return _apiFetch(`/api/projects/${projectId}/copilot/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, rating, comment }),
  });
}
