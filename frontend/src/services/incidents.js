/**
 * frontend/src/services/incidents.js
 * ===================================
 * API service for AIForge Day 21: Autonomous Incident Response & Self-Healing:
 * - Trigger Incident Detection Workflow
 * - List Incidents & Fetch Detail
 * - Approve Remediation Patch
 * - Fetch Incident Metrics
 * - Incident Q&A Chat Assistant
 * - Generate Post-Incident Summary Report
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

export async function triggerIncidentDetection(
  projectId = 'aiforge-demo',
  simDb = false,
  simPerf = false,
  simVal = false,
  simLoop = false
) {
  return _apiFetch(`/api/projects/${projectId}/incidents/detect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      simulate_db_failure: simDb,
      simulate_perf_failure: simPerf,
      simulate_validation_failure: simVal,
      simulate_repeated_loop: simLoop,
    }),
  });
}

export async function fetchIncidents(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/incidents`);
}

export async function fetchIncidentDetail(projectId = 'aiforge-demo', incidentId) {
  return _apiFetch(`/api/projects/${projectId}/incidents/${incidentId}`);
}

export async function approveRemediation(projectId = 'aiforge-demo', incidentId) {
  return _apiFetch(`/api/projects/${projectId}/incidents/${incidentId}/approve`, { method: 'POST' });
}

export async function fetchIncidentMetrics(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/incidents/metrics/summary`);
}

export async function askIncidentChat(projectId = 'aiforge-demo', question = 'Why did this incident happen?') {
  return _apiFetch(`/api/projects/${projectId}/incidents/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}

export async function fetchPostIncidentReport(projectId = 'aiforge-demo', incidentId) {
  return _apiFetch(`/api/projects/${projectId}/incidents/${incidentId}/report`);
}
