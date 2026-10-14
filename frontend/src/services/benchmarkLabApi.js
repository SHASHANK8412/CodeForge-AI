import { BACKEND_URL } from '../config/backend';

const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;

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
      'Content-Type': 'application/json',
      ..._getAuthHeader(),
      ...(opts.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  return res.json();
}

export async function fetchBenchmarkTasks() {
  return _apiFetch('/api/benchmark-lab/tasks');
}

export async function fetchBenchmarkModels(forceRefresh = false) {
  return _apiFetch(`/api/benchmark-lab/models?force_refresh=${forceRefresh}`);
}

export async function fetchBenchmarkConfigurations() {
  return _apiFetch('/api/benchmark-lab/configurations');
}

export async function createBenchmarkConfiguration(config) {
  return _apiFetch('/api/benchmark-lab/configurations', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function startBenchmarkRun(payload) {
  return _apiFetch('/api/benchmark-lab/runs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchBenchmarkRuns() {
  return _apiFetch('/api/benchmark-lab/runs');
}

export async function fetchBenchmarkRun(runId) {
  return _apiFetch(`/api/benchmark-lab/runs/${runId}`);
}

export async function cancelBenchmarkRun(runId) {
  return _apiFetch(`/api/benchmark-lab/runs/${runId}/cancel`, {
    method: 'POST',
  });
}

export async function compareBenchmarkRun(runId, priority, weights) {
  return _apiFetch('/api/benchmark-lab/compare', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId, priority, weights }),
  });
}

export async function fetchMarkdownReport(runId) {
  return _apiFetch(`/api/benchmark-lab/runs/${runId}/report`);
}

export async function fetchArtifactContent(runId, taskId, configId, filename) {
  const encodedFilename = encodeURIComponent(filename);
  return _apiFetch(`/api/benchmark-lab/runs/${runId}/artifacts/${taskId}/${configId}/${encodedFilename}`);
}

export async function fetchBenchmarkRecommendations() {
  return _apiFetch('/api/benchmark-lab/recommendations');
}
