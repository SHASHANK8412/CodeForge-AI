/**
 * frontend/src/services/browser_testing.js
 * =========================================
 * API service for AIForge Day 17: Autonomous Browser Testing & UI Validation:
 * - Run Browser Test Suite
 * - Fetch Latest Report
 * - Run AIForge Self-Test Suite
 * - Diagnose & Repair Browser Test Failures
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

export async function runBrowserTests(projectId = 'aiforge-demo', baseUrl = 'http://localhost:3000') {
  return _apiFetch(`/api/projects/${projectId}/browser-tests/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ base_url: baseUrl }),
  });
}

export async function fetchBrowserTestReport(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/browser-tests/report`);
}

export async function runAIForgeSelfTest(projectId = 'aiforge-demo') {
  return _apiFetch(`/api/projects/${projectId}/browser-tests/self-test`, { method: 'POST' });
}

export async function diagnoseBrowserFailure(projectId = 'aiforge-demo', scenarioId = 'scen_task_01') {
  return _apiFetch(`/api/projects/${projectId}/browser-tests/${scenarioId}/diagnose`, { method: 'POST' });
}
