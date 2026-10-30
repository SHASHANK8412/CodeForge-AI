/**
 * Quality Center: the project's report, computed by the backend from recorded checks only. Failed requests reject
 * with { status, error } (services/api.js) so the page shows the failure instead of placeholder data.
 */
import { BACKEND_URL } from '../config/backend';
import api from './api';
import { startVerification } from './executionGuardian';

export const fetchQualityReport = (generationId) =>
  api.get(`/api/projects/${encodeURIComponent(generationId)}/quality`, { timeout: 30000 });

/** "Repair" is a real Execution Guardian verification of the project: checks, then bounded repairs on a copy. */
export const triggerAutomaticRepair = (generationId) => startVerification(generationId, { max_repair_attempts: 3 });

export function exportQualityReport(generationId, format = 'pdf') {
  window.open(`${BACKEND_URL}/export/report/${generationId}?format=${format}`, '_blank');
}
