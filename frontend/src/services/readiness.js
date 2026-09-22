/**
 * frontend/src/services/readiness.js
 * ===================================
 * API service for AIForge Day 19: Autonomous Production Readiness Gate:
 * - Run Readiness Gate Check
 * - Fetch Readiness Report
 * - Approve / Reject Production Deployment
 * - Auto-Fix Readiness Blockers
 * - Fetch Readiness History & Version Diff
 * - Export Report JSON
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

export async function runReadinessGate(projectId = 'aiforge-demo', simulateSecurityBlock = false) {
  return _apiFetch(`/api/projects/${projectId}/readiness/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ simulate_security_block: simulateSecurityBlock }),
  });
}

export async function fetchReadinessReport(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/readiness/report`);
}

export async function approveDeployment(projectId = 'aiforge-demo', approver = 'Chief Architect') {
  return _apiFetch(`/api/projects/${projectId}/readiness/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approver }),
  });
}

export async function rejectDeployment(projectId = 'aiforge-demo', approver = 'Chief Architect') {
  return _apiFetch(`/api/projects/${projectId}/readiness/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approver }),
  });
}

export async function autofixReadinessBlockers(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/readiness/autofix`, { method: 'POST' });
}

export async function fetchReadinessHistory(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/readiness/history`);
}

export async function fetchReadinessDiff(projectId = 'aiforge-demo', v1 = 1, v2 = 2) {
  return _apiFetch(`/api/projects/${projectId}/readiness/diff?v1=${v1}&v2=${v2}`);
}

export async function exportReadinessReport(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/readiness/export`);
}
