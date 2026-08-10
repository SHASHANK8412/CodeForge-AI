/**
 * frontend/src/services/observability.js
 * ========================================
 * API service for AIForge Day 26: OpenTelemetry Observability & Distributed Tracing:
 * - Fetch Observability Metrics (Requests, Error Rate, P95, Active Incidents)
 * - Fetch Distributed Traces List
 * - Fetch Trace Detail & DNA Mapper
 * - Fetch Performance Regression Alerts
 * - Fetch Observability Readiness Status
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

export async function fetchObservabilityMetrics(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/observability/metrics`);
}

export async function fetchDistributedTraces(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/observability/traces`);
}

export async function fetchTraceDetail(projectId = 'aiforge-demo', traceId) {
  return _apiFetch(`/api/projects/${projectId}/observability/traces/${traceId}`);
}

export async function fetchPerformanceRegression(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/observability/regression`);
}

export async function fetchObservabilityReadiness(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/observability/readiness`);
}

// --- LEGACY COMPATIBILITY HELPERS ---

export async function fetchObservabilityData() {
  return _apiFetch(`/api/admin/observability`);
}

export async function fetchEvaluationData() {
  return _apiFetch(`/api/admin/evaluations`);
}

export async function submitFeedback(projectId, rating, comments) {
  return _apiFetch(`/api/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, rating, comments }),
  });
}
