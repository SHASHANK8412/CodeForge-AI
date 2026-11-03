import axios from 'axios';
import { BACKEND_URL } from '../config/backend';

// The backend requires a signed-in user on every API route. These hooks attach the current token
// to every backend request - axios (the shared instance and every axios.create() client) and plain
// fetch() - for backend URLs only, so the token never goes to another origin. The token is read
// on each request, so clients created before sign-in still send it afterwards.
const TOKEN_KEY = 'aiforge_jwt';

export function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function attachToken(config) {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token && isBackendUrl(axios.getUri(config))) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;   // always the current token, never a stale default
  }
  return config;
}

function headerValue(headers, name) {
  if (!headers) return undefined;
  if (typeof headers.get === 'function') return headers.get(name) ?? undefined;
  return headers[name] ?? headers[name.toLowerCase()];
}

/**
 * A request was answered 401. Sign out only if that request carried the token the app holds now: a request
 * that started before signing in (no token, or an older one) and fails afterwards must not end the new session.
 */
export function handleUnauthorized(sentAuthorization) {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token && sentAuthorization !== `Bearer ${token}`) return;
  localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new CustomEvent('aiforge:unauthorized'));
}

function reportUnauthorized(error) {
  if (error?.response?.status === 401) handleUnauthorized(headerValue(error.config?.headers, 'Authorization'));
  return Promise.reject(error);
}

function addAuthInterceptors(instance) {
  instance.interceptors.request.use(attachToken);
  instance.interceptors.response.use((res) => res, reportUnauthorized);
  return instance;
}

// Clients made with axios.create() at module load (before installAuthAxios runs) are covered too:
// this module patches axios.create as soon as it is imported, and main.jsx imports it first.
const originalCreate = axios.create.bind(axios);
if (!axios.create.__aiforgeAuth) {
  axios.create = (...args) => addAuthInterceptors(originalCreate(...args));
  axios.create.__aiforgeAuth = true;
  addAuthInterceptors(axios);
}

function isBackendUrl(input) {
  const url = typeof input === 'string' ? input : input?.url || String(input);
  try {
    return new URL(url, window.location.href).origin === new URL(BACKEND_URL, window.location.href).origin;
  } catch {
    return false;
  }
}

export function installAuthFetch() {
  if (typeof window === 'undefined' || window.fetch.__aiforgeAuth) return;
  const originalFetch = window.fetch.bind(window);

  const authFetch = async (input, init = {}) => {
    if (!isBackendUrl(input)) return originalFetch(input, init);
    const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`);
    const res = await originalFetch(input, { ...init, headers, credentials: init.credentials || 'include' });
    if (res.status === 401) handleUnauthorized(headers.get('Authorization') ?? undefined);
    return res;
  };
  authFetch.__aiforgeAuth = true;
  window.fetch = authFetch;
}
