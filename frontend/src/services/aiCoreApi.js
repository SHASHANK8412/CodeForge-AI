import { BACKEND_URL } from '../config/backend';
/**
 * AIForge AI Core — client API
 * ============================
 * Agent runs answered by the local Ollama models, and the list of installed models.
 * Errors (for example the model not answering) are thrown to the caller; no reply is invented.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;

// A local model can take minutes on a busy machine; the backend fails the run itself when the model gives up.
const RUN_TIMEOUT_MS = 15 * 60 * 1000;

export async function runAgent({ prompt, mode = "AGENT", modelId = null, projectId = null }) {
  const res = await axios.post(`${API_BASE}/api/ai-core/agents/run`, {
    prompt,
    mode,
    model_id: modelId || null,
    project_id: projectId || null
  }, { timeout: RUN_TIMEOUT_MS });
  return res.data.run;
}

export async function fetchAgentRuns(projectId) {
  const res = await axios.get(`${API_BASE}/api/ai-core/agents/runs`, { params: { project_id: projectId }, timeout: 4000 });
  return res.data?.runs || [];
}

/** The chat models installed in the local Ollama server ([] when it cannot be reached). */
export async function fetchModels() {
  const res = await axios.get(`${API_BASE}/api/ai-core/models`, { timeout: 8000 });
  return (res.data?.models || []).filter((m) => (m.capabilities || []).includes("CHAT"));
}
