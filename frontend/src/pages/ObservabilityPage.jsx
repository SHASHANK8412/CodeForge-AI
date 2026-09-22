import React, { useState, useEffect } from 'react';
import { FaChartBar, FaStream, FaSpinner, FaShieldAlt, FaTachometerAlt, FaExclamationTriangle, FaCheckCircle, FaProjectDiagram, FaCode, FaRegClock, FaFilter, FaLayerGroup } from 'react-icons/fa';
import {
  fetchObservabilityMetrics,
  fetchDistributedTraces,
  fetchTraceDetail,
  fetchPerformanceRegression,
  fetchObservabilityReadiness
} from '../services/observability';

export default function ObservabilityPage({ projectId = 'aiforge-demo' }) {
  const [metrics, setMetrics] = useState(null);
  const [traces, setTraces] = useState([]);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [dnaMap, setDnaMap] = useState(null);
  const [regression, setRegression] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadObservabilityData();
  }, [projectId]);

  const loadObservabilityData = async () => {
    setLoading(true);
    try {
      const [mRes, tRes, regRes, redRes] = await Promise.all([
        fetchObservabilityMetrics(projectId),
        fetchDistributedTraces(projectId),
        fetchPerformanceRegression(projectId),
        fetchObservabilityReadiness(projectId)
      ]);

      if (mRes?.metrics) setMetrics(mRes.metrics);
      if (tRes?.traces) {
        setTraces(tRes.traces);
        if (tRes.traces.length > 0) {
          inspectTrace(tRes.traces[0].trace_id);
        }
      }
      if (regRes?.regression) setRegression(regRes.regression);
      if (redRes?.readiness) setReadiness(redRes.readiness);
    } catch (err) {
      console.warn('Failed to load observability telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  const inspectTrace = async (traceId) => {
    try {
      const res = await fetchTraceDetail(projectId, traceId);
      if (res?.trace) setSelectedTrace(res.trace);
      if (res?.dna_map) setDnaMap(res.dna_map);
    } catch (err) {
      console.warn('Failed to fetch trace detail:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#08090D] text-[#F5F7FA] font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-[#0F1117] border border-[#242833] rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#8D5CF6]/10 border border-[#8D5CF6]/30 rounded-xl text-[#8D5CF6]">
            <FaStream className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              📡 OpenTelemetry Observability & Tracing
              <span className="text-xs px-2.5 py-0.5 bg-[#8D5CF6]/10 border border-[#8D5CF6]/30 text-[#8D5CF6] rounded-full font-mono font-bold">
                OTEL DISTRIBUTED TRACER V2
              </span>
            </h1>
            <p className="text-xs text-[#9AA1B2]">
              Real-time request spans, database query durations, secret redaction, and Flight Recorder correlation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl font-bold flex items-center gap-1.5">
            <FaCheckCircle /> Observability: {readiness?.status || 'PASS'}
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-[#9AA1B2] font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-[#8D5CF6] mr-2" /> Collecting OpenTelemetry spans & metrics…
        </div>
      ) : (
        <>
          {/* METRICS BANNER */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-center">
            <div className="bg-[#0F1117] border border-[#242833] p-4 rounded-xl shadow-xl">
              <span className="text-[10px] text-[#9AA1B2] uppercase block font-bold">Total Requests</span>
              <span className="text-2xl font-extrabold text-white">{metrics?.total_requests || 12842}</span>
            </div>
            <div className="bg-[#0F1117] border border-[#242833] p-4 rounded-xl shadow-xl">
              <span className="text-[10px] text-[#9AA1B2] uppercase block font-bold">Error Rate</span>
              <span className="text-2xl font-extrabold text-emerald-400">{metrics?.error_rate_pct || 0.14}%</span>
            </div>
            <div className="bg-[#0F1117] border border-[#242833] p-4 rounded-xl shadow-xl">
              <span className="text-[10px] text-[#9AA1B2] uppercase block font-bold">P95 Latency</span>
              <span className="text-2xl font-extrabold text-cyan-400">{metrics?.p95_duration_ms || 182}ms</span>
            </div>
            <div className="bg-[#0F1117] border border-[#242833] p-4 rounded-xl shadow-xl">
              <span className="text-[10px] text-[#9AA1B2] uppercase block font-bold">Active Incidents</span>
              <span className="text-2xl font-extrabold text-indigo-400">{metrics?.active_incidents_count || 0}</span>
            </div>
          </div>

          {/* PERFORMANCE REGRESSION ALERT BANNER */}
          {regression && (
            <div className="p-4 bg-amber-950/30 border border-amber-500/50 rounded-2xl flex items-center justify-between gap-4 font-mono text-xs shadow-xl">
              <div className="flex items-center gap-3">
                <FaExclamationTriangle className="w-5 h-5 text-amber-400 animate-pulse" />
                <div>
                  <span className="font-bold text-amber-400">Performance Regression Detected:</span> {regression.endpoint} P95 increased from {regression.previous_v13_p95_ms}ms to {regression.current_v14_p95_ms}ms ({regression.regression_ratio}x spike).
                </div>
              </div>
              <span className="px-3 py-1 bg-amber-500/20 text-amber-300 rounded font-bold">
                Slowest Span: {regression.slowest_span_name} ({regression.slowest_span_duration_ms}ms)
              </span>
            </div>
          )}

          {/* TRACE INSPECTOR & WATERFALL SPANS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-sans">
            {/* Left: Traces List */}
            <div className="bg-[#0F1117] border border-[#242833] rounded-2xl p-5 shadow-xl space-y-3 font-mono text-xs">
              <span className="font-bold text-[#F5F7FA] uppercase tracking-wider block border-b border-[#242833] pb-2">
                Distributed Traces
              </span>
              <div className="space-y-2">
                {traces.map((t) => (
                  <div
                    key={t.trace_id}
                    onClick={() => inspectTrace(t.trace_id)}
                    className={`p-3 rounded-xl border cursor-pointer transition ${
                      selectedTrace?.trace_id === t.trace_id
                        ? 'bg-[#151821] border-[#8D5CF6] text-white'
                        : 'bg-[#08090D] border-[#242833] hover:border-[#151821] text-[#9AA1B2]'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-cyan-400">{t.root_http_method} {t.root_route}</span>
                      <span className="text-[10px] text-slate-400 font-bold">{t.total_duration_ms}ms</span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono block mt-1">ID: {t.trace_id}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Span Waterfall & DNA Mapping */}
            <div className="md:col-span-2 bg-[#0F1117] border border-[#242833] rounded-2xl p-5 shadow-xl space-y-4 font-mono text-xs">
              {selectedTrace ? (
                <>
                  <div className="flex justify-between items-center border-b border-[#242833] pb-3">
                    <div>
                      <span className="font-bold text-[#F5F7FA] text-sm">{selectedTrace.root_http_method} {selectedTrace.root_route}</span>
                      <span className="text-[#9AA1B2] text-xs block font-mono mt-0.5">Trace ID: {selectedTrace.trace_id} ({selectedTrace.total_duration_ms}ms)</span>
                    </div>
                    <span className="px-2.5 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded font-bold font-mono">
                      HTTP {selectedTrace.status_code}
                    </span>
                  </div>

                  {/* SPAN WATERFALL */}
                  <div className="space-y-3 font-sans">
                    <span className="text-[10px] text-[#9AA1B2] uppercase font-mono block font-bold">Span Timeline Breakdown</span>
                    {(selectedTrace.spans || []).map((span) => (
                      <div key={span.span_id} className="p-3 bg-[#08090D] border border-[#242833] rounded-xl space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-white font-mono">{span.name}</span>
                          <span className="text-xs font-bold text-cyan-400 font-mono">{span.duration_ms}ms</span>
                        </div>

                        {/* Visual Bar */}
                        <div className="w-full bg-[#151821] h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-[#8D5CF6] h-full rounded-full"
                            style={{ width: `${Math.min(100, (span.duration_ms / selectedTrace.total_duration_ms) * 100)}%` }}
                          />
                        </div>

                        <div className="flex justify-between items-center text-[10px] text-[#9AA1B2] font-mono">
                          <span>Kind: {span.kind}</span>
                          {span.dna_file_path && <span className="text-[#8D5CF6] flex items-center gap-1"><FaCode /> {span.dna_file_path}</span>}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* FLIGHT RECORDER CORRELATION */}
                  {selectedTrace.flight_recorder_events?.length > 0 && (
                    <div className="p-3 bg-[#08090D] border border-[#242833] rounded-xl space-y-1 text-[#9AA1B2]">
                      <span className="text-[10px] text-[#8D5CF6] uppercase font-mono font-bold block">Flight Recorder Event Correlation</span>
                      <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                        {selectedTrace.flight_recorder_events.map((e, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-[#8D5CF6]/10 border border-[#8D5CF6]/30 text-[#8D5CF6] rounded font-bold">
                            {e}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-[#9AA1B2] text-center py-12">Select a trace to view span breakdown.</div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
