/**
 * AIForge Time Machine: the engineering event ledger, causal graph, historical replay, checkpoints,
 * restore preview / isolated restore / approved restore, the Regression Detective and experimental reruns.
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/time-machine`;
const long = { timeout: 120000 };

export const listEvents = (projectId, params) => api.get(`${base(projectId)}/events`, { params });
export const getEvent = (projectId, id) => api.get(`${base(projectId)}/events/${encodeURIComponent(id)}`);
export const listLegacyEvents = (projectId) => api.get(`${base(projectId)}/legacy`);
export const getGraph = (projectId, taskId) => api.get(`${base(projectId)}/graph`, { params: taskId ? { task_id: taskId } : {} });
export const getReplay = (projectId, taskId) => api.get(`${base(projectId)}/replay/${encodeURIComponent(taskId)}`);
export const compareEvents = (projectId, first, second) => api.get(`${base(projectId)}/compare`, { params: { first, second } });
export const createCheckpoint = (projectId, name) => api.post(`${base(projectId)}/checkpoints`, { name }, long);
export const listCheckpoints = (projectId) => api.get(`${base(projectId)}/checkpoints`);
export const previewRestore = (projectId, target) => api.post(`${base(projectId)}/restore/preview`, target, long);
export const restoreIsolated = (projectId, target) => api.post(`${base(projectId)}/restore/isolated`, target, { timeout: 600000 });
export const restoreApproved = (projectId, target, token) =>
  api.post(`${base(projectId)}/restore`, { ...target, token, approved: true }, { timeout: 600000 });
export const startInvestigation = (projectId) => api.post(`${base(projectId)}/investigations`, {}, long);
export const startRerun = (projectId, target) => api.post(`${base(projectId)}/reruns`, target, long);
export const listJobs = (projectId) => api.get(`${base(projectId)}/jobs`);
export const getJob = (projectId, id) => api.get(`${base(projectId)}/jobs/${encodeURIComponent(id)}`);
export const cancelJob = (projectId, id) => api.post(`${base(projectId)}/jobs/${encodeURIComponent(id)}/cancel`);
