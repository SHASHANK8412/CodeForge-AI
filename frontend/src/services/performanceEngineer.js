/**
 * AIForge Performance Engineer: static findings, measured baselines (app in the Docker sandbox),
 * optimization plans and before/after reports. Approval/execution use services/evolutionAutopilot.js.
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/performance`;
const long = { timeout: 30000 };

export const startPerfAnalysis = (projectId, body) => api.post(`${base(projectId)}/analyses`, body, long);
export const getLatestPerfAnalysis = (projectId) => api.get(`${base(projectId)}/analyses/latest`);
export const listPerfFindings = (projectId, params = {}) => api.get(`${base(projectId)}/findings`, { params });
export const startBaseline = (projectId, workload) => api.post(`${base(projectId)}/baselines`, { workload }, long);
export const listPerfRuns = (projectId) => api.get(`${base(projectId)}/runs`);
export const cancelPerfRun = (projectId, runId) => api.post(`${base(projectId)}/runs/${encodeURIComponent(runId)}/cancel`);
export const createPerfPlan = (projectId, body) => api.post(`${base(projectId)}/plans`, body, long);
export const listPerfPlans = (projectId) => api.get(`${base(projectId)}/plans`);
export const getPerfReport = (projectId, planId) => api.get(`${base(projectId)}/plans/${encodeURIComponent(planId)}/report`);
