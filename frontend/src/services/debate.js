/**
 * frontend/src/services/debate.js
 * =================================
 * API service for AIForge Day 16: Multi-Agent Architecture Debate:
 * - Start Multi-Agent Debate
 * - Fetch Latest Debate Session
 * - Fetch Debate History & ADRs
 * - Approve / Reject Decisions
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

export async function startMultiAgentDebate(projectId = 'aiforge-demo', requirement = 'Build a highly scalable social platform') {
  return _apiFetch('/api/debate/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, requirement, force_debate: true }),
  });
}

export async function fetchLatestDebate(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/debate/${projectId}/latest`);
}

export async function fetchDebateHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/debate/${projectId}/history`);
}

export async function fetchADRs(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/debate/${projectId}/adrs`);
}

export async function approveDebateDecision(projectId, debateId) {
  return _apiFetch(`/api/debate/${projectId}/${debateId}/approve`, { method: 'POST' });
}

export async function rejectDebateDecision(projectId, debateId) {
  return _apiFetch(`/api/debate/${projectId}/${debateId}/reject`, { method: 'POST' });
}
