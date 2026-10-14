/**
 * AIForge Autopilot: analyses, findings, improvement plans and validated executions of a project.
 * (The /api/autopilot autonomy controller is services/autopilot.js.)
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/evolution`;

export const listAutopilotProjects = () => api.get('/api/evolution/projects');

export const startAnalysis = (projectId, runTests = false) =>
  api.post(`${base(projectId)}/analyses`, { run_tests: runTests });
export const getLatestAnalysis = (projectId) => api.get(`${base(projectId)}/analyses/latest`);

export const listFindings = (projectId, params = {}) => api.get(`${base(projectId)}/findings`, { params });
export const setFindingDismissed = (projectId, findingId, dismissed) =>
  api.patch(`${base(projectId)}/findings/${encodeURIComponent(findingId)}`, { dismissed });

export const createPlan = (projectId, findingIds, objective = '') =>
  api.post(`${base(projectId)}/plans`, { finding_ids: findingIds, objective });
export const listPlans = (projectId) => api.get(`${base(projectId)}/plans`);
export const decidePlan = (projectId, planId, decision, body = {}) =>
  api.post(`${base(projectId)}/plans/${encodeURIComponent(planId)}/${decision}`, body);
export const executePlan = (projectId, planId, runTests = true) =>
  api.post(`${base(projectId)}/plans/${encodeURIComponent(planId)}/execute`, { run_tests: runTests });

export const listExecutions = (projectId) => api.get(`${base(projectId)}/executions`);
export const getExecution = (projectId, executionId) =>
  api.get(`${base(projectId)}/executions/${encodeURIComponent(executionId)}`);
export const cancelExecution = (projectId, executionId) =>
  api.post(`${base(projectId)}/executions/${encodeURIComponent(executionId)}/cancel`);
export const getExecutionReport = (projectId, executionId) =>
  api.get(`${base(projectId)}/executions/${encodeURIComponent(executionId)}/report`);
