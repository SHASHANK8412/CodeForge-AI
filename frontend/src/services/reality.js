/**
 * AIForge Reality Simulator: application model, scenario simulations (predict, or predict and run with approval),
 * cancellation, reports and prediction calibration. Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/reality`;
const long = { timeout: 120000 };

export const getApplicationModel = (projectId) => api.get(`${base(projectId)}/model`, long);
export const startSimulation = (projectId, scenario, runLoad) =>
  api.post(`${base(projectId)}/simulations`, { scenario, run_load: runLoad, approved: runLoad }, long);
export const listSimulations = (projectId) => api.get(`${base(projectId)}/simulations`);
export const getSimulation = (projectId, id) => api.get(`${base(projectId)}/simulations/${encodeURIComponent(id)}`);
export const cancelSimulation = (projectId, id) => api.post(`${base(projectId)}/simulations/${encodeURIComponent(id)}/cancel`);
export const getSimulationReport = (projectId, id, format) =>
  api.get(`${base(projectId)}/simulations/${encodeURIComponent(id)}/report`, { params: { format }, ...(format === 'markdown' ? { responseType: 'text' } : {}) });
export const getCalibration = () => api.get('/api/reality/calibration');
