/**
 * AIForge Security Guardian: assessments, findings with evidence, approved safe verification,
 * accepted risks, remediation plans (approved and executed through services/evolutionAutopilot.js),
 * remediation gates, history comparison and report export.
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/guardian`;
const long = { timeout: 60000 };

export const startGuardianAssessment = (projectId) => api.post(`${base(projectId)}/assessments`, {}, long);
export const listGuardianAssessments = (projectId) => api.get(`${base(projectId)}/assessments`);
export const getGuardianAssessment = (projectId, id) => api.get(`${base(projectId)}/assessments/${encodeURIComponent(id)}`);
export const abortGuardianJob = (projectId, id) => api.post(`${base(projectId)}/assessments/${encodeURIComponent(id)}/abort`);
export const listGuardianFindings = (projectId, filters = {}) => api.get(`${base(projectId)}/findings`, { params: filters });
export const getGuardianFinding = (projectId, id) => api.get(`${base(projectId)}/findings/${encodeURIComponent(id)}`);
export const verifyGuardianFindings = (projectId, findingIds) =>
  api.post(`${base(projectId)}/verifications`, { finding_ids: findingIds, approved: true }, long);
export const acceptGuardianRisk = (projectId, id, note) => api.post(`${base(projectId)}/findings/${encodeURIComponent(id)}/accept-risk`, { note });
export const createGuardianPlan = (projectId, id) => api.post(`${base(projectId)}/findings/${encodeURIComponent(id)}/plan`, {}, long);
export const getGuardianGate = (projectId, executionId) => api.get(`${base(projectId)}/gates/${encodeURIComponent(executionId)}`);
export const compareGuardianAssessments = (projectId, first, second) => api.get(`${base(projectId)}/compare`, { params: { first, second } });
export const getGuardianReport = (projectId, format) =>
  api.get(`${base(projectId)}/report`, { params: { format }, ...(format === 'markdown' ? { responseType: 'text' } : {}) });
