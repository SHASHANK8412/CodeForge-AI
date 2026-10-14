import { BACKEND_URL } from '../config/backend';
import axios from 'axios';

const API_BASE_URL = `${BACKEND_URL}`;

export async function fetchDeploymentStatus(generationId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${generationId}/deployment`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn(`Failed to fetch deployment status for ${generationId}:`, err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { project_id: generationId, project_name: null, status: 'UNAVAILABLE', error, provider: null, readiness: {}, providers: [], env_vars: [], config: {}, database: {}, urls: {}, health: {}, workflow: [], logs: [], history: [] };
  }
}

export async function validateDeployment(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/validate`, {}, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Validation error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { is_ready: false, readiness_score: null, checks: {}, error };
  }
}

export async function startDeployment(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/start`, {}, { timeout: 15000 });
    return res.data;
  } catch (err) {
    console.error('Start deployment error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { success: false, status: 'FAILED', error };
  }
}

export async function cancelDeployment(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/cancel`, {}, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Cancel deployment error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { success: false, error };
  }
}

export async function checkHealth(generationId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${generationId}/deployment/health`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Check health error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { status: 'UNKNOWN', frontend: 'UNKNOWN', backend: 'UNKNOWN', database: 'UNKNOWN', api: 'UNREACHABLE', error, last_checked: new Date().toLocaleTimeString() };
  }
}

export async function fetchDeploymentHistory(generationId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${generationId}/deployment/history`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('History error:', err);
    return { history: [] };
  }
}

export async function fetchDeploymentPlan(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/plan`, {}, { timeout: 15000 });
    return res.data;
  } catch (err) {
    console.error('Plan error:', err);
    return null;
  }
}

export async function executeApprovedDeployment(generationId, providers = ['Vercel', 'Render']) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/deploy`, {
      approved: true,
      providers
    }, { timeout: 25000 });
    return res.data;
  } catch (err) {
    console.error('Execute deploy error:', err);
    throw err;
  }
}

export async function diagnoseDeploymentFailure(generationId, logs = [], errorMessage = '') {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/diagnose`, {
      logs,
      error_message: errorMessage
    }, { timeout: 15000 });
    return res.data;
  } catch (err) {
    console.error('Diagnose error:', err);
    return null;
  }
}

export async function rollbackDeployment(generationId, targetVersion = 'v1') {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/deployment/rollback`, {
      target_version: targetVersion
    }, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Rollback error:', err);
    return null;
  }
}

export async function updateEnvironmentVariables(generationId, envVars) {
  try {
    const res = await axios.put(`${API_BASE_URL}/api/projects/${generationId}/deployment/env`, {
      env_vars: envVars
    }, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Update env error:', err);
    return null;
  }
}

