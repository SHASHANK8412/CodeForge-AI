/**
 * frontend/src/services/rag.js
 * =============================
 * API service for project RAG knowledge management, document upload, deletion, stats, and debug queries.
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

/**
 * Upload project documentation files.
 */
export async function uploadProjectDocuments(projectId, files) {
  const formData = new FormData();
  Array.from(files).forEach((f) => formData.append('files', f));

  const res = await fetch(`${API_BASE}/api/projects/${projectId}/rag/upload`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
    headers: {
      ..._getAuthHeader(),
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Upload failed');
  }

  return res.json();
}

/**
 * Delete a specific document chunk.
 */
export async function deleteProjectDocument(projectId, documentId) {
  return _apiFetch(`/api/projects/${projectId}/rag/documents/${documentId}`, {
    method: 'DELETE',
  });
}

/**
 * Fetch RAG knowledge statistics for project.
 */
export async function fetchProjectRAGStats(projectId) {
  return _apiFetch(`/api/projects/${projectId}/rag/stats`);
}

/**
 * Perform debug RAG retrieval.
 */
export async function debugRAGQuery(projectId, agent, query) {
  return _apiFetch(`/api/rag/debug`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, agent, query }),
  });
}
