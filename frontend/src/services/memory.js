/**
 * frontend/src/services/memory.js
 * =================================
 * API service for AIForge Day 22: Long-Term Engineering Memory & Knowledge Graph:
 * - Remember Engineering Knowledge
 * - Fetch Engineering Memories
 * - Search Memory
 * - Fetch Knowledge Graph
 * - Fetch Memory Quality Dashboard
 * - Consolidate Memories
 * - Update Memory Version
 * - Compatibility helpers (fetchProjectMemory, searchProjectMemory, explainDecision)
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

export async function createMemory(
  projectId = 'aiforge-demo',
  title,
  content,
  type = 'ARCHITECTURE_DECISION',
  source = 'DEBATE'
) {
  return _apiFetch(`/api/projects/${projectId}/memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, type, source }),
  });
}

export async function fetchMemories(projectId = 'aiforge-demo', activeOnly = true) {
  return _apiFetch(`/api/projects/${projectId}/memory?active_only=${activeOnly}`);
}

export async function searchMemories(projectId = 'aiforge-demo', query = '') {
  return _apiFetch(`/api/projects/${projectId}/memory/search?q=${encodeURIComponent(query)}`);
}

export async function fetchKnowledgeGraph(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/memory/graph`);
}

export async function fetchMemoryDashboard(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/memory/dashboard`);
}

export async function consolidateMemories(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/memory/consolidate`, { method: 'POST' });
}

export async function updateMemoryVersion(projectId = 'aiforge-demo', memoryId, newContent, reason = 'Migration') {
  return _apiFetch(`/api/projects/${projectId}/memory/${memoryId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_content: newContent, reason }),
  });
}

// Backward Compatibility Helpers for Day 12 UI Components
export async function fetchProjectMemory(projectId = 'aiforge-demo') {
  const res = await fetchMemories(projectId, false);
  return {
    memories: res.memories || [],
    decisions: (res.memories || []).filter(m => m.type === 'ARCHITECTURE_DECISION'),
  };
}

export async function searchProjectMemory(projectId = 'aiforge-demo', query = '') {
  const res = await searchMemories(projectId, query);
  return {
    memories: res.memories || [],
    query,
  };
}

export async function explainDecision(projectId = 'aiforge-demo', topic = '') {
  const res = await searchMemories(projectId, topic);
  const top = res.memories?.[0];
  return {
    topic,
    explanation: top
      ? `Decision: ${top.title}. Reason: ${top.content}`
      : `AIForge evaluated architectural trade-offs for ${topic} based on project requirements.`,
  };
}
