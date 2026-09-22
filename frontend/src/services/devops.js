/**
 * frontend/src/services/devops.js
 * ================================
 * API service for AIForge Day 20: Autonomous DevOps & Deployment Engine:
 * - Fetch Deployment Plan
 * - Trigger Autonomous Project Deployment
 * - Fetch Deployment Status
 * - Fetch Deployment History & Comparisons
 * - Fetch Production Health Metrics
 * - Trigger Automated Version Rollback
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

export async function fetchDeploymentPlan(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/devops/plan`, { method: 'POST' });
}

export async function deployProject(
  projectId = 'aiforge-demo',
  simulateHealthFailure = false,
  simulateSmokeFailure = false,
  bypassReadiness = false
) {
  return _apiFetch(`/api/projects/${projectId}/devops/deploy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      simulate_health_failure: simulateHealthFailure,
      simulate_smoke_failure: simulateSmokeFailure,
      bypass_readiness: bypassReadiness,
    }),
  });
}

export async function fetchDeploymentStatus(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/devops/status`);
}

export async function fetchDeploymentHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/devops/history`);
}

export async function compareDeployments(projectId = 'aiforge-demo', v1 = 1, v2 = 2) {
  return _apiFetch(`/api/projects/${projectId}/devops/compare?v1=${v1}&v2=${v2}`);
}

export async function fetchProductionHealth(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/devops/production-health`);
}

export async function rollbackDeployment(projectId = 'aiforge-demo', targetVersion = 1) {
  return _apiFetch(`/api/projects/${projectId}/devops/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_version: targetVersion }),
  });
}
