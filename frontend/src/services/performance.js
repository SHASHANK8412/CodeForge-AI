/**
 * frontend/src/services/performance.js
 * =====================================
 * API service for AIForge Day 18: Autonomous Performance Engineer:
 * - Fetch Performance Report
 * - Profile Project
 * - Run Autonomous Optimization
 * - Fetch Performance History
 * - Simulate Performance What-If
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

export async function fetchPerformanceReport(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/performance/report`);
}

export async function profilePerformance(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/performance/profile`, { method: 'POST' });
}

export async function optimizePerformanceAutomatically(projectId = 'aiforge-demo', simulateRegression = false) {
  return _apiFetch(`/api/projects/${projectId}/performance/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ simulate_regression: simulateRegression }),
  });
}

export async function fetchPerformanceHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/performance/history`);
}

export async function simulatePerformanceWhatIf(projectId = 'aiforge-demo', proposedOptimization = 'Add Redis caching') {
  return _apiFetch(`/api/projects/${projectId}/performance/simulate-whatif`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ proposed_optimization: proposedOptimization }),
  });
}
