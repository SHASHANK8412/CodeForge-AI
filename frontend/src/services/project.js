import { BACKEND_URL } from '../config/backend';
import axios from 'axios';

const API_BASE_URL = `${BACKEND_URL}`;

// A failed request is reported as a failure, never replaced with sample results.
const errorText = (err) => err?.response?.data?.detail || err?.message || 'Request failed';

export async function fetchProjectFiles(generationId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/projects/${generationId}/files`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn('Failed to fetch project files:', err);
    return { project_id: generationId, project_name: null, files: [], error: errorText(err) };
  }
}

export async function runProject(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/run`, {}, { timeout: 120000 });
    return res.data;
  } catch (err) {
    console.error('Run project error:', err);
    return { status: 'ERROR', exit_code: 1, stdout: '', stderr: errorText(err), error: errorText(err) };
  }
}

export async function testProject(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/test`, {}, { timeout: 300000 });
    return res.data;
  } catch (err) {
    console.error('Test project error:', err);
    return { status: 'ERROR', passed: 0, failed: 0, total: 0, output: errorText(err), failures: [], error: errorText(err) };
  }
}

export async function reviewProject(generationId) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/projects/${generationId}/review`, {}, { timeout: 300000 });
    return res.data;
  } catch (err) {
    console.error('Review project error:', err);
    return { overall_score: null, scores: {}, issues: [], security_passed: null, error: errorText(err) };
  }
}

export async function askAssistant(message, fileContext = '', selectedCode = '') {
  try {
    const promptPayload = `Project Context:\nFile: ${fileContext}\nSelected Code:\n${selectedCode}\n\nUser Question:\n${message}`;
    const res = await axios.post(`${API_BASE_URL}/chat/message`, { message: promptPayload }, { timeout: 120000 });
    return res.data?.response || 'The assistant returned an empty response.';
  } catch (err) {
    console.error('Assistant API error:', err);
    return `The assistant is unavailable: ${errorText(err)}`;
  }
}

export async function saveProjectFile(projectId, path, content) {
  const res = await axios.put(`${API_BASE_URL}/api/project/${projectId}/file`, { path, content }, { timeout: 10000 });
  return res.data;
}

export async function runSelectedCodeReview(projectId, path, selectedCode, action) {
  const res = await axios.post(`${API_BASE_URL}/api/project/${projectId}/review-selection`, { path, selected_code: selectedCode, action }, { timeout: 15000 });
  return res.data;
}

export async function proposeFix(projectId, issue) {
  const res = await axios.post(`${API_BASE_URL}/api/project/${projectId}/propose-fix`, {
    file: issue.file || issue.path || '',
    line: issue.line || issue.line_number || 1,
    category: issue.category || 'CODE_QUALITY',
    title: issue.title || issue.message || 'Issue',
    description: issue.description || issue.message || 'Defect',
    suggested_fix: issue.suggested_fix || ''
  }, { timeout: 15000 });
  return res.data;
}

export async function applyFix(projectId, file, content) {
  const res = await axios.post(`${API_BASE_URL}/api/project/${projectId}/apply-fix`, { file, content }, { timeout: 10000 });
  return res.data;
}

export async function fetchSnapshots(projectId) {
  const res = await axios.get(`${API_BASE_URL}/api/project/${projectId}/snapshots`, { timeout: 10000 });
  return res.data;
}

export async function rollbackSnapshot(projectId, versionId) {
  const res = await axios.post(`${API_BASE_URL}/api/project/${projectId}/rollback`, { version_id: versionId }, { timeout: 10000 });
  return res.data;
}

export async function runAutonomousRepair(projectId) {
  const res = await axios.post(`${API_BASE_URL}/api/project/${projectId}/auto-repair`, {}, { timeout: 45000 });
  return res.data;
}

export async function fetchProjectProblems(projectId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/project/${projectId}/problems`, { timeout: 10000 });
    return res.data?.problems || [];
  } catch (err) {
    return [];
  }
}

export async function fetchProjectChanges(projectId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/project/${projectId}/changes`, { timeout: 10000 });
    return res.data?.changes || [];
  } catch (err) {
    return [];
  }
}

export async function fetchAgentTimeline(projectId) {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/project/${projectId}/timeline`, { timeout: 10000 });
    return res.data?.events || [];
  } catch (err) {
    return [];
  }
}

