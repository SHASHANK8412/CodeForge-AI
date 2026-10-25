/**
 * AIForge Reality Simulator: application model, scenario simulations (predict, or predict and run with approval),
 * experiment plans to approve, cancellation, reports and prediction calibration. Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/reality`;
const long = { timeout: 120000 };

export const getApplicationModel = (projectId) => api.get(`${base(projectId)}/model`, long);
export const previewExperimentPlan = (projectId, scenario, runLoad) =>
  api.post(`${base(projectId)}/plan`, { scenario, run_load: runLoad });
// a load run is approved together with the exact experiment plan that was shown (its hash)
export const startSimulation = (projectId, scenario, runLoad, planHash = null) =>
  api.post(`${base(projectId)}/simulations`, { scenario, run_load: runLoad, approved: runLoad, plan_hash: runLoad ? planHash : null }, long);
export const listSimulations = (projectId) => api.get(`${base(projectId)}/simulations`);
export const getSimulation = (projectId, id) => api.get(`${base(projectId)}/simulations/${encodeURIComponent(id)}`);
export const cancelSimulation = (projectId, id) => api.post(`${base(projectId)}/simulations/${encodeURIComponent(id)}/cancel`);
export const getSimulationReport = (projectId, id, format) =>
  api.get(`${base(projectId)}/simulations/${encodeURIComponent(id)}/report`, { params: { format }, ...(format === 'markdown' ? { responseType: 'text' } : {}) });
export const getCalibration = () => api.get('/api/reality/calibration');
