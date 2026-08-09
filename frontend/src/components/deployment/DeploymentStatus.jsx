import React from 'react';
import { FaCheckCircle, FaExternalLinkAlt, FaRedo, FaCode, FaRocket } from 'react-icons/fa';

export default function DeploymentStatus({ status = 'LIVE', urls = {}, onRedeploy }) {
  const isLive = status.toUpperCase() === 'LIVE';

  if (!isLive) return null;

  const frontendUrl = urls.frontend || 'https://fooddelivery-app.vercel.app';
  const backendUrl = urls.backend || 'https://fooddelivery-api.onrender.com';
  const docsUrl = urls.api_docs || `${backendUrl}/docs`;

  return (
    <div className="bg-gradient-to-tr from-slate-950 via-indigo-950/40 to-slate-950 border border-emerald-500/40 rounded-2xl p-6 shadow-2xl font-sans mb-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center text-2xl shrink-0">
            <FaCheckCircle />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-extrabold text-white tracking-tight">🎉 Deployment Successful</h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase">● LIVE</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Your application is live and receiving traffic across global Edge CDN nodes.
            </p>
          </div>
        </div>

        {/* Live URL Pill Badges */}
        <div className="flex flex-col sm:flex-row gap-3 text-xs font-mono">
          <a
            href={frontendUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500 text-cyan-400 flex items-center gap-1.5 transition"
          >
            <span>Frontend: {frontendUrl}</span>
            <FaExternalLinkAlt className="w-2.5 h-2.5" />
          </a>

          <a
            href={backendUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-purple-500 text-purple-400 flex items-center gap-1.5 transition"
          >
            <span>Backend: {backendUrl}</span>
            <FaExternalLinkAlt className="w-2.5 h-2.5" />
          </a>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-800/80">
        <a
          href={frontendUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-emerald-500 to-cyan-600 hover:from-emerald-400 hover:to-cyan-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-emerald-500/20"
        >
          <FaExternalLinkAlt className="w-3.5 h-3.5" /> Open Application
        </a>

        <a
          href={docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition"
        >
          <FaCode className="w-3.5 h-3.5 text-cyan-400" /> Open OpenAPI Docs
        </a>

        <button
          onClick={onRedeploy}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition"
        >
          <FaRedo className="w-3.5 h-3.5 text-amber-400" /> Redeploy
        </button>

        <button
          onClick={onRedeploy}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition"
        >
          <FaRocket className="w-3.5 h-3.5 text-purple-400" /> Infrastructure Logs
        </button>
      </div>
    </div>
  );
}
