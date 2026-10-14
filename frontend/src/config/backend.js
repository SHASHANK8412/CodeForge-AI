// Single source of truth for where the browser reaches the AIForge backend.
// Set VITE_API_URL at build time when the frontend is hosted separately (Docker, Vercel, ...).
export const BACKEND_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
