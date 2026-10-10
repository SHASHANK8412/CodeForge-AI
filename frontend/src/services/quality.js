import { BACKEND_URL } from '../config/backend';
import axios from 'axios';

const API_BASE_URL = `${BACKEND_URL}`;

export async function fetchQualityReport(generationId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${generationId}/quality`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn(`Failed to fetch quality report for ${generationId}:`, err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { project_id: generationId, project_name: null, overall_score: null, status: 'UNAVAILABLE', error, categories: {}, quality_gates: [], passed_gates_count: 0, total_gates_count: 0, tests: null, test_breakdown: [], security: {}, performance: {}, reviewer_findings: [], testing_findings: [], recommendations: [] };
  }
}

export async function triggerAutomaticRepair(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/evaluate`, {
      requirements: 'Project self-repair execution',
      max_repair_attempts: 3
    }, { timeout: 25000 });
    return res.data;
  } catch (err) {
    console.error('Repair workflow error:', err);
    const error = err?.response?.data?.detail || err?.message || 'Request failed';
    return { status: 'ERROR', error, score: null, repair_attempts: 0, max_repair_attempts: 3, test_results: null, repaired_files: [] };
  }
}

export function exportQualityReport(generationId, format = 'pdf') {
  window.open(`${API_BASE_URL}/export/report/${generationId}?format=${format}`, '_blank');
}
