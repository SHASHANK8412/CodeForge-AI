import { BACKEND_URL } from '../config/backend';

// The backend requires a signed-in user on every API route. axios already sends the token
// (services/auth.js sets its default header); this does the same for the plain fetch() calls,
// for backend URLs only, so the token never goes to another origin.
const TOKEN_KEY = 'aiforge_jwt';

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
    if (res.status === 401) window.dispatchEvent(new CustomEvent('aiforge:unauthorized'));
    return res;
  };
  authFetch.__aiforgeAuth = true;
  window.fetch = authFetch;
}
