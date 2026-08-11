import axios from 'axios';
import { getGeneration } from './generation';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function fetchGenerationStatus(generationId) {
  try {
    return await getGeneration(generationId);
  } catch (err) {
    console.warn('Workspace generation status failed:', err);
    return null;
  }
}

export async function fetchGitOverview(projectId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/github/overview`, {
      params: { project_id: projectId },
      timeout: 10000,
    });
    return res.data;
  } catch (err) {
    console.warn('Workspace git overview failed:', err);
    return null;
  }
}

export async function fetchPreviewStatus(projectId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/preview/status`, {
      timeout: 10000,
    });
    return res.data;
  } catch (err) {
    return null;
  }
}

export async function fetchPreviewLogs(projectId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/preview/logs`, {
      timeout: 10000,
    });
    return res.data;
  } catch (err) {
    return null;
  }
}
