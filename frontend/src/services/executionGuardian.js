/**
 * AIForge Execution Guardian: start a verification of a generated project (it runs on an isolated copy), follow
 * its checks and repairs, cancel it, and fetch the report. Failed requests reject with { status, error }
 * (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/verifications`;
const long = { timeout: 120000 };

export const startVerification = (projectId, settings = {}, requirements = '') =>
  api.post(base(projectId), { settings, requirements }, long);
export const listVerifications = (projectId) => api.get(base(projectId));
export const getVerification = (projectId, id) => api.get(`${base(projectId)}/${encodeURIComponent(id)}`);
export const getVerificationChecks = (projectId, id) => api.get(`${base(projectId)}/${encodeURIComponent(id)}/checks`);
export const getVerificationRepairs = (projectId, id) => api.get(`${base(projectId)}/${encodeURIComponent(id)}/repairs`);
export const getVerificationReport = (projectId, id, format = 'json') =>
  api.get(`${base(projectId)}/${encodeURIComponent(id)}/report`, { params: { format }, ...(format === 'markdown' ? { responseType: 'text' } : {}) });
export const cancelVerification = (projectId, id) => api.post(`${base(projectId)}/${encodeURIComponent(id)}/cancel`);
