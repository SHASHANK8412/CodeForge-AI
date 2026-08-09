/**
 * frontend/src/services/dna.js
 * =============================
 * API service for AIForge Day 15: Engineering DNA & Dependency Intelligence:
 * - Fetch Engineering DNA Graph
 * - Impact Analysis
 * - Requirement Traceability
 * - Dead Code Detection
 * - Circular Dependency Detection
 * - Graph Diffing & Node Explanation
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

export async function fetchDNAGraph(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/dna/${projectId}/graph`);
}

export async function runImpactAnalysis(projectId = 'aiforge-demo', nodeId = 'PaymentService', changeType = 'modify') {
  return _apiFetch(`/api/projects/${projectId}/impact-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ node_id: nodeId, change_type: changeType }),
  });
}

export async function fetchRequirementTrace(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/dna/${projectId}/requirements-trace`);
}

export async function fetchDeadCode(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/dna/${projectId}/dead-code`);
}

export async function fetchCircularDependencies(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/dna/${projectId}/circular-dependencies`);
}

export async function fetchGraphDiff(projectId = 'aiforge-demo', v1 = 1, v2 = 2) {
  return _apiFetch(`/api/dna/${projectId}/diff?v1=${v1}&v2=${v2}`);
}

export async function explainGraphNode(projectId = 'aiforge-demo', nodeId = 'PaymentService') {
  return _apiFetch(`/api/dna/${projectId}/explain-node`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ node_id: nodeId }),
  });
}
