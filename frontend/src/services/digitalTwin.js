/**
 * AIForge Digital Twin: dependency graph, read-only impact simulations, and prediction vs. actual.
 * Approval and execution of a report's plan go through the Autopilot API (services/evolutionAutopilot.js).
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/twin`;

export const startTwinAnalysis = (projectId) => api.post(`${base(projectId)}/analyses`);
export const getLatestTwinAnalysis = (projectId) => api.get(`${base(projectId)}/analyses/latest`);
export const getTwinGraph = (projectId, params = {}) => api.get(`${base(projectId)}/graph`, { params });
export const getDependencies = (projectId, node, params = {}) =>
  api.get(`${base(projectId)}/dependencies`, { params: { node, ...params } });

export const simulateChange = (projectId, body) => api.post(`${base(projectId)}/simulations`, body);
export const listImpactReports = (projectId) => api.get(`${base(projectId)}/reports`);
export const getImpactReport = (projectId, reportId) =>
  api.get(`${base(projectId)}/reports/${encodeURIComponent(reportId)}`);
export const createPlanFromReport = (projectId, reportId, option = 0) =>
  api.post(`${base(projectId)}/reports/${encodeURIComponent(reportId)}/plan`, { option });
export const getReportOutcome = (projectId, reportId) =>
  api.get(`${base(projectId)}/reports/${encodeURIComponent(reportId)}/outcome`);
export const getTwinAccuracy = (projectId) => api.get(`${base(projectId)}/accuracy`);
