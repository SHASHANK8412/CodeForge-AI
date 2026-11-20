import { BACKEND_URL } from '../config/backend';

/**
 * Voice input: the recording is transcribed by the backend on this machine (POST /api/speech/transcribe).
 * The sign-in token is added by the global fetch patch (src/authFetch.js).
 */
const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;

export async function transcribeAudio(blob, language) {
  const form = new FormData();
  const type = (blob.type || 'audio/webm').split(';')[0];
  const ext = { 'audio/webm': 'webm', 'audio/ogg': 'ogg', 'audio/mp4': 'm4a', 'audio/wav': 'wav' }[type] || 'webm';
  form.append('audio', new File([blob], `prompt.${ext}`, { type }));
  if (language) form.append('language', language);
  const res = await fetch(`${API_BASE}/api/speech/transcribe`, { method: 'POST', body: form });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `Transcription failed (${res.status})`);
  }
  return body; // { text, language, duration_seconds }
}
