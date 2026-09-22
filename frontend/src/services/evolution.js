/**
 * frontend/src/services/evolution.js
 * ===================================
 * API service for AIForge Day 24: Autonomous Software Evolution Engine:
 * - Analyze Project Evolution
 * - Fetch Technical Debt Score & Items
 * - Fetch Evolution Roadmap (NOW / NEXT / LATER)
 * - Implement Recommendation
 * - Fetch Evolution History & Debt Trend
 * - Set User Goal
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

export async function analyzeEvolution(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/evolution/analyze`);
}

export async function fetchTechnicalDebt(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/evolution/debt`);
}

export async function fetchRoadmap(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/evolution/roadmap`);
}

export async function implementRecommendation(projectId = 'aiforge-demo', recId, simFailure = false) {
  return _apiFetch(`/api/projects/${projectId}/evolution/recommendations/${recId}/implement`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ simulate_failure: simFailure }),
  });
}

export async function fetchEvolutionHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/evolution/history`);
}

export async function setEvolutionGoal(projectId = 'aiforge-demo', goal = 'Enterprise Deployment') {
  return _apiFetch(`/api/projects/${projectId}/evolution/goal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal }),
  });
}
