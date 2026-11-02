import axios from 'axios';
import { BACKEND_URL } from '../config/backend';

/**
 * The Ollama models installed on this machine and the ones the pipeline will use.
 * Resolves to { ollama_online, models, planning_model, coding_model } or { error }.
 */
export async function fetchInstalledModels() {
  try {
    const res = await axios.get(`${BACKEND_URL}/api/models/installed`, { timeout: 10000 });
    return res.data;
  } catch (err) {
    return { ollama_online: false, models: [], planning_model: null, coding_model: null, error: err?.message || 'Request failed' };
  }
}
