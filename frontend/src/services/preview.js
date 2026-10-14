/**
 * Live preview of a generated project. The backend runs it only in hardened Docker containers
 * and reports a service as "running" only after an HTTP probe answered.
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/preview`;

export const getPreviewStatus = (projectId) => api.get(`${base(projectId)}/status`);
export const getPreviewLogs = (projectId) => api.get(`${base(projectId)}/logs`);
export const startPreview = (projectId) => api.post(`${base(projectId)}/start`);
export const stopPreview = (projectId) => api.post(`${base(projectId)}/stop`);
