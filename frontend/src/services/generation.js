/**
 * frontend/src/services/generation.js
 * =====================================
 * All generation-related API calls and SSE streaming.
 *
 * Functions
 * ---------
 * createGeneration(projectId, prompt)    — POST /api/generations
 * getGeneration(generationId)            — GET  /api/generations/{id}
 * getGenerationEvents(id, opts)          — GET  /api/generations/{id}/events
 * connectGenerationStream(id, callbacks) — SSE + polling fallback
 * cancelGeneration(generationId)         — POST /api/generations/{id}/cancel
 * listGenerations()                      — GET  /api/generations
 *
 * SSE + Polling fallback
 * ----------------------
 * connectGenerationStream() tries SSE first. If the connection drops or
 * is not supported, it automatically falls back to polling every 2 s.
 * When SSE reconnects successfully, polling stops.
 * Returns a { disconnect } object to clean up on component unmount.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/** Returns the JWT token stored by the auth flow. */
function _getAuthHeader() {
  const token = localStorage.getItem('aiforge_jwt');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Shared fetch with auth headers. Throws on non-OK responses. */
async function _apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ..._getAuthHeader(),
      ...(opts.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) { /* ignore parse error */ }
    throw new Error(detail);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// REST helpers
// ---------------------------------------------------------------------------

/**
 * Create a new generation and start it immediately.
 * @param {string} projectId
 * @param {string} prompt
 * @returns {Promise<{generation_id: string, status: string}>}
 */
export async function createGeneration(projectId, prompt) {
  return _apiFetch('/api/generations', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, prompt }),
  });
}

/**
 * Get the current status and agent list for a generation.
 * @param {string} generationId
 * @returns {Promise<object>}
 */
export async function getGeneration(generationId) {
  return _apiFetch(`/api/generations/${generationId}`);
}

// Backwards-compatible alias
export const fetchGenerationStatus = getGeneration;

/**
 * Get chronological events for a generation.
 * @param {string} generationId
 * @param {{offset?: number, limit?: number}} opts
 */
export async function getGenerationEvents(generationId, { offset = 0, limit = 100 } = {}) {
  return _apiFetch(
    `/api/generations/${generationId}/events?offset=${offset}&limit=${limit}`,
  );
}

/**
 * Cancel a running generation.
 * @param {string} generationId
 */
export async function cancelGeneration(generationId) {
  return _apiFetch(`/api/generations/${generationId}/cancel`, { method: 'POST' });
}

/**
 * List all generations for the authenticated user.
 */
export async function listGenerations() {
  return _apiFetch('/api/generations');
}

// ---------------------------------------------------------------------------
// Terminal status check
// ---------------------------------------------------------------------------

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled']);

export function isTerminalStatus(status) {
  return TERMINAL_STATUSES.has(status?.toLowerCase?.() ?? status);
}

// ---------------------------------------------------------------------------
// SSE + Polling fallback
// ---------------------------------------------------------------------------

/**
 * Connect to the real-time generation stream.
 *
 * @param {string} generationId
 * @param {{
 *   onSnapshot?: (status: object) => void,
 *   onEvent?: (event: object) => void,
 *   onAgentStarted?: (agent: string, event: object) => void,
 *   onAgentCompleted?: (agent: string, event: object) => void,
 *   onAgentFailed?: (agent: string, event: object) => void,
 *   onGenerationCompleted?: (event: object) => void,
 *   onGenerationFailed?: (event: object) => void,
 *   onError?: (err: Error) => void,
 *   pollIntervalMs?: number,
 * }} callbacks
 *
 * @returns {{ disconnect: () => void }}
 */
export const subscribeToGenerationEvents = connectGenerationStream;

export function connectGenerationStream(generationId, callbacks = {}) {
  const {
    onSnapshot,
    onEvent,
    onAgentStarted,
    onAgentCompleted,
    onAgentFailed,
    onGenerationCompleted,
    onGenerationFailed,
    onError,
    pollIntervalMs = 2000,
  } = callbacks;

  let es = null;         // EventSource
  let pollTimer = null;  // setInterval handle for polling fallback
  let sseActive = false;
  let destroyed = false;

  // ----- Dispatch helper -----
  function dispatch(rawEvent) {
    const type = rawEvent.type || rawEvent.event_type || '';
    const agent = rawEvent.agent;

    if (typeof onEvent === 'function') onEvent(rawEvent);

    switch (type) {
      case 'snapshot':
        if (typeof onSnapshot === 'function') onSnapshot(rawEvent);
        break;
      case 'agent_started':
        if (typeof onAgentStarted === 'function') onAgentStarted(agent, rawEvent);
        break;
      case 'agent_completed':
        if (typeof onAgentCompleted === 'function') onAgentCompleted(agent, rawEvent);
        break;
      case 'agent_failed':
        if (typeof onAgentFailed === 'function') onAgentFailed(agent, rawEvent);
        break;
      case 'generation_completed':
        if (typeof onGenerationCompleted === 'function') onGenerationCompleted(rawEvent);
        break;
      case 'generation_failed':
        if (typeof onGenerationFailed === 'function') onGenerationFailed(rawEvent);
        break;
      default:
        break;
    }
  }

  // ----- Polling fallback -----
  async function poll() {
    if (destroyed || sseActive) return;
    try {
      const status = await getGeneration(generationId);
      dispatch({ type: 'snapshot', ...status });
      if (isTerminalStatus(status.status)) {
        stopPolling();
      }
    } catch (err) {
      if (typeof onError === 'function') onError(err);
    }
  }

  function startPolling() {
    if (pollTimer) return;
    poll(); // immediate first call
    pollTimer = setInterval(poll, pollIntervalMs);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // ----- SSE setup -----
  function connectSSE() {
    if (destroyed) return;

    const token = localStorage.getItem('aiforge_jwt') || '';
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    const url = `${API_BASE}/api/generations/${generationId}/stream${tokenParam}`;

    try {
      es = new EventSource(url, { withCredentials: true });
    } catch (_) {
      // Browser doesn't support EventSource → polling only
      startPolling();
      return;
    }

    es.onopen = () => {
      sseActive = true;
      stopPolling(); // SSE connected — stop polling
    };

    const eventTypes = [
      'snapshot', 'agent_started', 'agent_progress', 'agent_log',
      'agent_completed', 'agent_failed', 'agent_retrying',
      'generation_started', 'generation_completed', 'generation_failed',
      'generation_cancelled', 'repair_started', 'repair_completed',
      'testing_started', 'testing_completed', 'stream_done', 'heartbeat',
    ];

    eventTypes.forEach((evtType) => {
      es.addEventListener(evtType, (e) => {
        if (evtType === 'heartbeat') return;
        if (evtType === 'stream_done') {
          sseActive = false;
          es?.close();
          es = null;
          return;
        }
        try {
          const data = JSON.parse(e.data || '{}');
          dispatch({ type: evtType, ...data });
        } catch (_) { /* malformed JSON */ }
      });
    });

    es.onerror = () => {
      sseActive = false;
      es?.close();
      es = null;
      if (destroyed) return;

      // Polling fallback while SSE is down
      startPolling();

      // Attempt SSE reconnect after 5 s
      setTimeout(() => {
        if (!destroyed) connectSSE();
      }, 5000);
    };
  }

  // ----- Bootstrap -----
  getGeneration(generationId)
    .then((status) => {
      if (typeof onSnapshot === 'function') onSnapshot(status);
      if (!isTerminalStatus(status.status)) {
        connectSSE();
        startPolling(); // bridge gap while SSE connects
        setTimeout(() => { if (sseActive) stopPolling(); }, 3000);
      }
    })
    .catch((err) => {
      if (typeof onError === 'function') onError(err);
      startPolling();
    });

  // ----- Disconnect -----
  function disconnect() {
    destroyed = true;
    sseActive = false;
    stopPolling();
    if (es) { es.close(); es = null; }
  }

  return { disconnect };
}

// Backwards-compatible alias
export const subscribeToGenerationSSE = (generationId, onEvent, onError) =>
  connectGenerationStream(generationId, { onEvent, onError }).disconnect;
