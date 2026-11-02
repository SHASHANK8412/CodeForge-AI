/**
 * AIForge Chaos Engineer: controlled failure experiments in an isolated sandbox, resilience reports,
 * and repair plans (approved and executed through services/evolutionAutopilot.js).
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/chaos`;
const long = { timeout: 60000 };

export const listChaosScenarios = () => api.get('/api/chaos/scenarios');
export const runChaosPreflight = (projectId, config) => api.post(`${base(projectId)}/preflight`, config, long);
export const createChaosAssessment = (projectId, config) => api.post(`${base(projectId)}/assessments`, config, long);
export const listChaosAssessments = (projectId) => api.get(`${base(projectId)}/assessments`);
export const getChaosAssessment = (projectId, id) => api.get(`${base(projectId)}/assessments/${encodeURIComponent(id)}`);
export const approveChaosAssessment = (projectId, id) => api.post(`${base(projectId)}/assessments/${encodeURIComponent(id)}/approve`, {}, long);
export const abortChaosAssessment = (projectId, id) => api.post(`${base(projectId)}/assessments/${encodeURIComponent(id)}/abort`);
export const compareChaosAssessments = (projectId, first, second) => api.get(`${base(projectId)}/compare`, { params: { first, second } });
export const listChaosFindings = (projectId) => api.get(`${base(projectId)}/findings`);
export const createChaosPlan = (projectId, findingId) => api.post(`${base(projectId)}/findings/${encodeURIComponent(findingId)}/plan`, {}, long);
export const getChaosGate = (projectId, executionId) => api.get(`${base(projectId)}/gates/${encodeURIComponent(executionId)}`);
