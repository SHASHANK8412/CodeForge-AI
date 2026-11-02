/**
 * AIForge Evolution Engine: opportunities, experiment plans, approved runs, candidate comparison,
 * approval bound to the source revision and patch, promotion, and Engineering Memory.
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/evolution-engine`;
const long = { timeout: 60000 };
const exp = (projectId, id) => `${base(projectId)}/experiments/${encodeURIComponent(id)}`;

export const discoverOpportunities = (projectId, criteria) => api.post(`${base(projectId)}/opportunities/discover`, { criteria: criteria || {} }, long);
export const listOpportunities = (projectId) => api.get(`${base(projectId)}/opportunities`);
export const planExperiment = (projectId, body) => api.post(`${base(projectId)}/experiments`, body, long);
export const listExperiments = (projectId) => api.get(`${base(projectId)}/experiments`);
export const getExperiment = (projectId, id) => api.get(exp(projectId, id));
export const runExperiment = (projectId, id) => api.post(`${exp(projectId, id)}/run`, { approved: true }, long);
export const abortExperiment = (projectId, id) => api.post(`${exp(projectId, id)}/abort`);
export const approveCandidate = (projectId, id, candidateId) => api.post(`${exp(projectId, id)}/approve`, { candidate_id: candidateId }, long);
export const promoteExperiment = (projectId, id) => api.post(`${exp(projectId, id)}/promote`, {}, long);
export const getEngineeringMemory = (projectId) => api.get(`${base(projectId)}/memory`);
