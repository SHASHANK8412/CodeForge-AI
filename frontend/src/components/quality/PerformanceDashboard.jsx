import React from 'react';
import { FaTachometerAlt } from 'react-icons/fa';

export default function PerformanceDashboard({ performance = {} }) {
  const apiLatency = performance.api_latency_ms ? `${performance.api_latency_ms} ms` : 'Not measured';
  const avgResponse = performance.average_response_ms ? `${performance.average_response_ms} ms` : 'Not measured';
  const slowestEndpoint = performance.slowest_endpoint_ms ? `${performance.slowest_endpoint_ms} ms` : 'Not measured';
  const memory = performance.memory_mb ? `${performance.memory_mb} MB` : 'Not measured';
  const buildTime = performance.build_time_seconds ? `${performance.build_time_seconds} sec` : 'Not measured';

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaTachometerAlt className="text-amber-400" /> Performance & Runtime Latency Metrics
        </h3>
        <span className="font-mono text-xs font-bold text-amber-400">
          Latency: {apiLatency}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">API Latency</div>
          <div className="text-base font-black text-emerald-400 font-mono mt-1">{apiLatency}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Avg Response</div>
          <div className="text-base font-black text-cyan-400 font-mono mt-1">{avgResponse}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Slowest Route</div>
          <div className="text-base font-black text-amber-400 font-mono mt-1">{slowestEndpoint}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Memory Usage</div>
          <div className="text-base font-black text-purple-400 font-mono mt-1">{memory}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Build Time</div>
          <div className="text-base font-black text-indigo-400 font-mono mt-1">{buildTime}</div>
        </div>
      </div>
    </div>
  );
}
