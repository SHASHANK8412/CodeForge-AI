/**
 * AIForge Integration & Compatibility Engine: a project's shared contract (versions, diffs, agent slices) and its
 * compatibility runs (static analysis, or verification with generated contract tests and bounded repairs).
 * Failed requests reject with { status, error, raw } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}`;
const long = { timeout: 120000 };

export const getContract = (projectId, params = {}) => api.get(`${base(projectId)}/contract`, { params });
export const listContractVersions = (projectId) => api.get(`${base(projectId)}/contract/versions`);
export const getContractDiff = (projectId, from, to) =>
  api.get(`${base(projectId)}/contract/diff`, { params: { ...(from ? { from } : {}), ...(to ? { to } : {}) } });
export const deriveContract = (projectId, reason) => api.post(`${base(projectId)}/contract/derive`, reason ? { reason } : {});
export const registerContract = (projectId, contract, reason) => api.post(`${base(projectId)}/contract`, { contract, reason });

export const analyzeIntegration = (projectId) => api.post(`${base(projectId)}/integration/analyze`, {}, long);
export const verifyIntegration = (projectId, settings = {}) => api.post(`${base(projectId)}/integration/verify`, { settings }, long);
export const listIntegrationRuns = (projectId) => api.get(`${base(projectId)}/integration/runs`);
export const getIntegrationRun = (projectId, runId) => api.get(`${base(projectId)}/integration/runs/${encodeURIComponent(runId)}`);
export const getIntegrationReport = (projectId, runId, format = 'json') =>
  api.get(`${base(projectId)}/integration/runs/${encodeURIComponent(runId)}/report`,
    { params: { format }, ...(format === 'markdown' ? { responseType: 'text' } : {}) });
export const cancelIntegrationRun = (projectId, runId) =>
  api.post(`${base(projectId)}/integration/runs/${encodeURIComponent(runId)}/cancel`);

/** The validation errors a 422 carries (the shared client only keeps a generic message). */
export const errorsOf = (e) => e?.raw?.response?.data?.detail?.errors || [];
