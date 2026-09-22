/**
 * frontend/src/services/intelligence.js
 * ========================================
 * API service for AIForge Extraordinary Features:
 * - What-If Engineering Simulator
 * - AI Engineering DNA Graph
 * - Autonomous Bug Bounty Security Hunter
 * - Multi-Agent Debate Arena
 * - Talk to Your Software Assistant
 * - Production Readiness CTO Gate
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

// 1. What-If Simulator
export async function runSimulation(projectId, proposedChange) {
  return _apiFetch('/api/simulator/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, proposed_change: proposedChange }),
  });
}

// 2. DNA Graph
export async function fetchDnaGraph(projectId) {
  return _apiFetch(`/api/dna/${projectId}/graph`);
}

export async function analyzeDnaImpact(projectId, targetComponent) {
  return _apiFetch('/api/dna/impact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, target_node_or_component: targetComponent }),
  });
}

// 3. Bug Bounty
export async function scanSecurityHunter(projectId) {
  return _apiFetch(`/api/bug-bounty/scan?project_id=${projectId}`, { method: 'POST' });
}

export async function fetchSecurityReport(projectId) {
  return _apiFetch(`/api/bug-bounty/${projectId}/report`);
}

// 4. Multi-Agent Debate
export async function startDebate(generationId, prompt) {
  return _apiFetch(`/api/debate/start?generation_id=${generationId}&prompt=${encodeURIComponent(prompt)}`, { method: 'POST' });
}

export async function fetchDebateVerdict(generationId) {
  return _apiFetch(`/api/debate/${generationId}`);
}

// 5. Talk to Your Software
export async function chatSoftwareAssistant(projectId, query) {
  return _apiFetch('/api/software-assistant/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, query }),
  });
}

// 6. Production Readiness CTO Gate
export async function fetchCtoGateReport(projectId) {
  return _apiFetch(`/api/production-gate/${projectId}`);
}

export async function overrideCtoGate(projectId) {
  return _apiFetch(`/api/production-gate/${projectId}/override`, { method: 'POST' });
}
