import { BACKEND_URL } from '../config/backend';
import axios from 'axios';

const API_BASE_URL = `${BACKEND_URL}`;

export async function fetchProjects({ page = 1, pageSize = 12, search = '', status = 'all', sort = 'recently_updated' } = {}) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects`, {
      params: { page, page_size: pageSize, search, status, sort },
      timeout: 10000
    });
    return res.data;
  } catch (err) {
    console.warn('Failed to fetch projects list:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { projects: [], page, page_size: pageSize, total: 0, error, stats: { total_projects: 0, completed: 0, building: 0, deployed: 0, avg_quality_score: null, total_tests_passed: null, successful_deployments: 0 } };
  }
}

export async function fetchProjectDetails(generationId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${generationId}`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn(`Failed to fetch project details for ${generationId}:`, err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { generation_id: generationId, project_name: generationId, description: '', status: 'UNAVAILABLE', error, quality_score: null, tests: null, stack: {}, created_at: null, updated_at: null, activity: [], versions: [] };
  }
}

export async function renameProject(generationId, newName) {
  try {
    const res = await axios.patch(`${API_BASE_URL}/api/projects/${generationId}`, { name: newName }, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Rename project error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { success: false, error };
  }
}

export async function duplicateProject(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/duplicate`, {}, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Duplicate project error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { success: false, error };
  }
}

export async function archiveProject(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/archive`, {}, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Archive project error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { success: false, error };
  }
}

export async function deleteProject(generationId) {
  try {
    const res = await axios.delete(`${API_BASE_URL}/api/projects/${generationId}`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.error('Delete project error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { success: false, error };
  }
}
