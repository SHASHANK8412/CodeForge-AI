/**
 * frontend/src/services/security.js
 * ====================================
 * API service for AIForge Security Foundation Layer:
 * - Security Scanning
 * - Fetch Security Report
 * - Mark False Positive
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

export async function runSecurityScan(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/security/scan?project_id=${projectId}`, { method: 'POST' });
}

export async function fetchSecurityReport(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/security/${projectId}/report`);
}

export async function markFalsePositive(projectId, findingId, reason) {
  return _apiFetch(`/api/security/${projectId}/false-positive`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ finding_id: findingId, reason }),
  });
}
