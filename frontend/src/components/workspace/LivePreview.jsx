import React, { useCallback, useEffect, useState } from 'react';
import { FaPlay, FaStop, FaRedo, FaExternalLinkAlt, FaTerminal } from 'react-icons/fa';
import { getPreviewLogs, getPreviewStatus, startPreview, stopPreview } from '../../services/preview';

const BUSY = new Set(['starting', 'installing', 'building']);

const TONE = {
  running: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  partial: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  failed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  unavailable: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
};
const tone = (s) => TONE[s] || (BUSY.has(s) ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30' : 'bg-slate-800 text-slate-400 border-slate-700');
const label = (s) => (s || 'not started').replace(/_/g, ' ');

function Badge({ status }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tone(status)}`}>
      {BUSY.has(status) && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {label(status)}
    </span>
  );
}

function Service({ name, svc }) {
  if (!svc) return null;
  return (
    <div className="min-w-0 rounded-xl bg-bg-base/60 px-3 py-2.5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] uppercase tracking-wide text-text-muted">{name}</p>
        <Badge status={svc.status} />
      </div>
      {svc.url ? (
        <a href={svc.url} target="_blank" rel="noreferrer"
           className="mt-1 flex items-center gap-1.5 truncate font-mono text-xs text-cyan-300 hover:text-cyan-200">
          {svc.url} <FaExternalLinkAlt className="h-2.5 w-2.5 shrink-0" />
        </a>
      ) : (
        <p className="mt-1 truncate text-xs text-text-muted">{svc.status === 'not_previewable' ? 'nothing to run' : 'no verified URL'}</p>
      )}
      {svc.probe && <p className="mt-0.5 truncate text-[10px] text-emerald-400/80">verified: {svc.probe}</p>}
      {svc.error && svc.status !== 'not_previewable' && <p className="mt-0.5 text-[11px] text-rose-300 break-words">{svc.error}</p>}
      {svc.status === 'not_previewable' && svc.error && <p className="mt-0.5 text-[10px] text-text-muted">{svc.error}</p>}
    </div>
  );
}

/**
 * Live preview of a generated app on the Build page. Everything shown comes from the preview API:
 * a service has a link only after the backend's HTTP probe got an answer from its container.
 */
export default function LivePreview({ generationId }) {
  const [preview, setPreview] = useState(null);
  const [logs, setLogs] = useState({ backend: '', frontend: '' });
  const [logTab, setLogTab] = useState('backend');
  const [showLogs, setShowLogs] = useState(false);
  const [error, setError] = useState('');
  const [acting, setActing] = useState(false);

  const refresh = useCallback(async () => {
    if (!generationId) return;
    try {
      setPreview(await getPreviewStatus(generationId));
      setLogs(await getPreviewLogs(generationId));
    } catch (e) {
      setError(e?.error || 'Could not load preview status.');
    }
  }, [generationId]);

  const status = preview?.status || 'not_started';
  const busy = BUSY.has(status) || [preview?.backend?.status, preview?.frontend?.status].some((s) => BUSY.has(s));

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (!busy) return undefined;
    const t = setInterval(refresh, 2500);
    return () => clearInterval(t);
  }, [busy, refresh]);

  const run = async (action) => {
    setActing(true);
    setError('');
    try {
      setPreview(await action(generationId));
      await refresh();
    } catch (e) {
      setError(e?.error || 'Request failed.');
    } finally {
      setActing(false);
    }
  };

  const active = busy || status === 'running' || status === 'partial';
  const expires = preview?.expires_at && active ? new Date(preview.expires_at * 1000).toLocaleTimeString() : null;
  const logText = logs?.[logTab] || '';

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Live preview</h3>
          <Badge status={status} />
        </div>
        <div className="flex items-center gap-2">
          {active ? (
            <button onClick={() => run(stopPreview)} disabled={acting}
                    className="flex items-center gap-1.5 rounded-lg bg-rose-600/90 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-500 disabled:opacity-50">
              <FaStop className="h-2.5 w-2.5" /> Stop
            </button>
          ) : (
            <button onClick={() => run(startPreview)} disabled={acting}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600/90 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50">
              {preview && status !== 'not_started' ? <FaRedo className="h-2.5 w-2.5" /> : <FaPlay className="h-2.5 w-2.5" />}
              {preview && status !== 'not_started' ? 'Restart' : 'Run preview'}
            </button>
          )}
          <button onClick={() => setShowLogs((v) => !v)}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800">
            <FaTerminal className="h-2.5 w-2.5" /> Logs
          </button>
        </div>
      </div>

      {status === 'not_started' && (
        <p className="text-xs text-text-muted">
          Runs the generated app in an isolated Docker container (non-root, read-only, local-only port).
          Links appear only after the app answers.
        </p>
      )}
      {preview?.reason && <p className="mb-2 text-xs text-amber-300">{preview.reason}</p>}
      {error && <p className="mb-2 text-xs text-rose-300">{error}</p>}

      {preview && status !== 'not_started' && (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <Service name="Backend" svc={preview.backend} />
          <Service name="Frontend" svc={preview.frontend} />
        </div>
      )}
      {expires && <p className="mt-2 text-[10px] text-text-muted">Stops automatically at {expires}.</p>}

      {showLogs && (
        <div className="mt-3">
          <div className="mb-1.5 flex gap-1">
            {['backend', 'frontend'].map((t) => (
              <button key={t} onClick={() => setLogTab(t)}
                      className={`rounded-md px-2 py-0.5 text-[11px] capitalize ${logTab === t ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}>
                {t}
              </button>
            ))}
          </div>
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/50 p-3 font-mono text-[11px] leading-relaxed text-slate-300">
            {logText || 'No container output yet.'}
          </pre>
        </div>
      )}
    </section>
  );
}
