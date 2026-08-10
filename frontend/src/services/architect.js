/**
 * frontend/src/services/architect.js
 * ===================================
 * API service for AIForge Day 25: AI Software Architect Simulator:
 * - Fetch Current Architecture Diagram
 * - Simulate Architecture Scenario
 * - Simulate Failure Propagation
 * - Trigger Multi-Agent Architecture Debate
 * - Approve Scenario & Generate 7-Phase Plan & ADR
 * - Fetch Architecture History
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

export async function fetchCurrentArchitecture(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/architect/current`);
}

export async function simulateArchitecture(projectId = 'aiforge-demo', prompt = 'Should we add Redis?') {
  return _apiFetch(`/api/projects/${projectId}/architect/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
}

export async function simulateFailure(projectId = 'aiforge-demo', componentName = 'PostgreSQL') {
  return _apiFetch(`/api/projects/${projectId}/architect/failure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ component_name: componentName }),
  });
}

export async function runArchitectDebate(projectId = 'aiforge-demo', topic = 'Should we introduce Redis caching?') {
  return _apiFetch(`/api/projects/${projectId}/architect/debate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic }),
  });
}

export async function approveArchitecturePlan(projectId = 'aiforge-demo', scenarioId) {
  return _apiFetch(`/api/projects/${projectId}/architect/approve?scenario_id=${scenarioId}`, {
    method: 'POST',
  });
}

export async function fetchArchitectureHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/architect/history`);
}
