/**
 * AIForge Swarm Intelligence: missions (task graph, artifacts, messages, conflicts, gates), the agent registry,
 * approval to run, human decisions on escalated conflicts, cancellation and delivery (an Autopilot plan).
 * Failed requests reject with { status, error } (see services/api.js).
 */
import api from './api';

const base = (projectId) => `/api/projects/${encodeURIComponent(projectId)}/swarm/missions`;
const long = { timeout: 120000 };

export const listSwarmAgents = () => api.get('/api/swarm/agents');
export const createMission = (projectId, body) => api.post(base(projectId), body, long);
export const listMissions = (projectId) => api.get(base(projectId));
export const getMission = (projectId, id) => api.get(`${base(projectId)}/${encodeURIComponent(id)}`);
export const runMission = (projectId, id) => api.post(`${base(projectId)}/${encodeURIComponent(id)}/run`, { approved: true }, long);
export const cancelMission = (projectId, id) => api.post(`${base(projectId)}/${encodeURIComponent(id)}/cancel`);
export const decideConflict = (projectId, id, conflictId, proposalId) =>
  api.post(`${base(projectId)}/${encodeURIComponent(id)}/decide`, { conflict_id: conflictId, proposal_id: proposalId }, long);
export const deliverMission = (projectId, id) => api.post(`${base(projectId)}/${encodeURIComponent(id)}/deliver`, {}, long);
